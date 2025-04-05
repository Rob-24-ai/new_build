"""
Handles conversation context management for ArtSensei
Maintains the history of user inputs, AI responses, and images
"""

class ConversationContext:
    """Manages conversation context between the user and AI"""
    
    def __init__(self):
        """Initialize an empty conversation history"""
        self.messages = []
        self.current_image = None
    
    def add_user_message(self, text):
        """Add a user text message to the conversation"""
        self.messages.append({
            "role": "user",
            "content": text
        })
    
    def add_image_message(self, image_data_url):
        """Add an image message to the conversation"""
        # Store the current image being discussed
        self.current_image = image_data_url
        
        # Also add to the messages to maintain context
        self.messages.append({
            "role": "user",
            "content": "[User shared an image for analysis]"
        })
    
    def add_ai_response(self, text):
        """Add an AI response to the conversation"""
        self.messages.append({
            "role": "assistant",
            "content": text
        })
    
    def get_conversation_history(self, max_messages=10):
        """Get recent conversation history as a formatted string"""
        # Get the most recent messages, limited to max_messages
        recent_messages = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        
        # Format the conversation for Gemini prompt
        formatted_conversation = ""
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_conversation += f"{role}: {msg['content']}\n"
        
        return formatted_conversation
    
    def get_prompt_with_context(self, prompt, include_image=False):
        """Create a prompt that includes conversation history"""
        context = self.get_conversation_history()
        
        if context:
            final_prompt = f"""
Previous conversation:
{context}

User's new question: {prompt}

Please respond to the question in the context of our conversation.
"""
            return final_prompt
        else:
            # No history yet
            return prompt
