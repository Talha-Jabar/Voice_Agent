import os
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from Database.customer_database import get_customer_by_id, update_customer_data, get_random_customer
from Support_Classes.conversation_manager import ConversationManager
import json
from pydantic import Field, BaseModel
from typing import Optional, List, Union

class UpdateCustomerDetailsInput(BaseModel):
        customer_id: str = Field(..., description="The customer ID to update")
        field_to_update: Optional[str] = Field(None, description="The field to update (location, payment_method, etc.)")
        new_value: Optional[Union[str, List[str]]] = Field(None, description="The new value for the field")
        json_input: Optional[str] = Field(None, description="Alternative JSON input containing all parameters")


class VoiceAgentOrchestrator:
    def __init__(self, openai_api_key):
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.conversation_manager = ConversationManager()
        self.current_customer = None
        self.setup_tools()
        self.setup_agent()

    def setup_tools(self):
        """Setup LangChain tools for the agent"""
        
        def get_customer_info(customer_id: str) -> str:
            """Get customer information by ID"""
            customer = get_customer_by_id(customer_id)
            if customer:
                return json.dumps(customer, indent=2)
            return "Customer not found"
        

        def update_customer_info(customer_id: str, updates: str) -> str:
            """Update customer information"""
            try:
                update_data = json.loads(updates)
                success = update_customer_data(customer_id, update_data)
                return "Customer updated successfully" if success else "Failed to update customer"
            except json.JSONDecodeError:
                return "Invalid update data format"

        def add_complaint(customer_id: str, complaint: str) -> str:
            """Add a complaint for a customer"""
            import uuid
            complaint_id = f"COMP{str(uuid.uuid4())[:8].upper()}"
            update_data = {
                "complain": complaint,
                "complain_id": complaint_id,
                "status": "complaint_received"
            }
            success = update_customer_data(customer_id, update_data)
            return f"Complaint recorded with ID: {complaint_id}" if success else "Failed to record complaint"
        
        # In langchain_agent.py, within the setup_tools method, add this new tool:

        def update_customer_details(
            customer_id: str,
                field_to_update: Optional[str] = None,
                new_value: Optional[Union[str, List[str]]] = None,
                json_input: Optional[str] = None
            ) -> str:
            """Update specific customer details like location, payment method, or products."""
            allowed_fields = [
                "location", "payment_method", "product(s)", 
                "name", "paid_status", "status"
            ]
            
            try:
                # Handle JSON input if provided
                if json_input:
                    try:
                        data = json.loads(json_input)
                        customer_id = data.get("customer_id", customer_id)
                        field_to_update = data.get("field_to_update", field_to_update)
                        new_value = data.get("new_value", new_value)
                    except json.JSONDecodeError:
                        return "Error: Invalid JSON format for update data"
                
                if not field_to_update or not new_value:
                    return "Error: Must provide either field_to_update and new_value parameters or valid json_input"
                
                if field_to_update not in allowed_fields:
                    return f"Error: Cannot update {field_to_update}. Allowed fields: {', '.join(allowed_fields)}"
                
                # Handle special cases
                if field_to_update == "product(s)":
                    if not isinstance(new_value, list):
                        new_value = [new_value]
                
                update_data = {field_to_update: new_value}
                success = update_customer_data(customer_id, update_data)
                
                if success:
                    return f"Successfully updated {field_to_update} to {new_value}"
                return "Failed to update customer details"
            except Exception as e:
                return f"Error: {str(e)}"
        
        def get_conversation_history() -> str:
            """Get current conversation history"""
            history = self.conversation_manager.get_history()
            return json.dumps(history, indent=2)

        self.tools = [
            Tool(
                name="get_customer_info",
                description="Get customer information by customer ID",
                func=get_customer_info
            ),
            Tool(
                name="update_customer_info", 
                description="Update customer information with new data",
                func=update_customer_info
            ),
            Tool(
                name="update_customer_details",
                description="""Update specific customer details like location, payment method, or products. "
                            "Input can be either three parameters (customer_id, field_to_update, new_value) "
                            "or a JSON string with these fields in json_input parameter.""",
                func=update_customer_details,
                args_schema=UpdateCustomerDetailsInput 
            ),

            Tool(
                name="add_complaint",
                description="Add a complaint for a customer",
                func=add_complaint
            ),
            Tool(
                name="get_conversation_history",
                description="Get the current conversation history",
                func=get_conversation_history
            )
        ]

    def setup_agent(self):
        """Setup the LangChain agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Smith, a customer service representative for RichDaddy Incorporation, a grocery company. 
            You are conducting follow-up calls with customers about their orders.
            
            Your goals:
            1. Greet customers warmly and professionally
            2. Confirm order details and delivery information
            3. Address any complaints or concerns
            4. Update customer records as needed
            5. Change customer information if the relevant customer asks for it
            6. Maintain a helpful and empathetic tone
            
            When successfully updating customer information:
            - First confirm the update was successful
            - Then ask if there's anything else you can help with
            - Before it seems customer have asked all their questions or requests then take review from the customer about the relative product.
            
            Available tools:
            - get_customer_info: Get customer details by ID
            - update_customer_info: Update customer information
            - update_customer_details: Update specific fields like location, payment method, or products
            - add_complaint: Record customer complaints
            - get_conversation_history: View conversation history
            
            When updating customer details:
            - Verify the changes with the customer before applying them
            - For payment method changes, confirm the new payment details
            - For location changes, verify the new address
            - For product changes, check availability first
            
            Always be polite, professional, and solution-oriented. If a customer has a complaint, 
            acknowledge it, gather details, and work toward a resolution."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )

    def start_conversation(self):
        """Start a conversation with a random customer"""
        self.current_customer = get_random_customer()
        if not self.current_customer:
            return "No customers available in database"
        
        # Initialize conversation with customer context
        initial_context = f"Starting call with customer {self.current_customer['name']} (ID: {self.current_customer['customer_id']}) regarding order {self.current_customer['order_id']}"
        
        greeting = f"Hello, this is Smith from RichDaddy Incorporation. How are you doing today, {self.current_customer['name']}?"
        
        self.conversation_manager.add_message("agent", greeting)
        return greeting

    def process_user_input(self, user_input: str) -> str:
        """Process user input through the LangChain agent"""
        self.conversation_manager.add_message("user", user_input)
        
        if not self.current_customer:
            error_response = "No customer is currently selected. Please start a conversation first."
            self.conversation_manager.add_message("agent", error_response)
            return error_response

        context = f"Current customer: {self.current_customer['name']} (ID: {self.current_customer['customer_id']})\n"
        context += f"Order ID: {self.current_customer['order_id']}\n"
        context += f"User said: {user_input}"
        
        try:
            response = self.agent_executor.invoke({"input": context})
            agent_response = response["output"]
            
            # Check if the response indicates a successful update
            if "successfully updated" in agent_response.lower():
                agent_response += "\n\nIs there anything else I can help you with today?"
                
            self.conversation_manager.add_message("agent", agent_response)
            return agent_response
        except Exception as e:
            # Only show technical difficulties message for unexpected errors
            if "error" in str(e).lower():
                error_response = "I apologize, but I'm having some technical difficulties. Could you please repeat that?"
            else:
                error_response = "Thank you for that information. Is there anything else I can help you with today?"
            self.conversation_manager.add_message("agent", error_response)
            return error_response

    def end_conversation(self):
        """End the conversation and update customer database"""
        if not self.current_customer:
            return "No active conversation to end"
        
        summary = self.conversation_manager.get_summary()
        
        # Update customer database with conversation results
        update_data = {
            "conversation_history": summary["history"],
            "sentiment": summary["sentiment"],
            "last_contact": "2025-08-08 10:30:00"  # Current timestamp
        }
        
        if summary["complaint"]:
            update_data["complain"] = summary["complaint"]
            update_data["status"] = "complaint_received"
        
        update_customer_data(self.current_customer["customer_id"], update_data)
        
        return {
            "customer": self.current_customer["name"],
            "summary": summary,
            "database_updated": True
        }

