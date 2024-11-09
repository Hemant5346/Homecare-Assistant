
from chatbot_types import CHATBOT_TYPES
from config import MAX_HISTORY,MAX_TOKENS



def get_system_prompt(bot_type):
    return CHATBOT_TYPES[bot_type]["system_prompt"]

def get_assistant_prompt(bot_type):
    return CHATBOT_TYPES[bot_type]["assistant_prompt"]


def chat_with_gpt(client, prompt, conversation_history, pdf_chain=None, bot_type=None):
    if not client:
        return "OpenAI client is not initialized. Please check your API key in the .env file."
    
    try:
        system_prompt = get_system_prompt(bot_type)
        assistant_prompt = get_assistant_prompt(bot_type)
        
        if pdf_chain:
            system_prompt += " Use the information from the uploaded PDF to provide detailed and accurate answers. If the PDF doesn't contain relevant information for a question, use your general knowledge but mention that the information is not from the PDF."
            chain_history = [(msg["content"], "") for msg in conversation_history[-MAX_HISTORY:] if msg["role"] == "user"]
            response = pdf_chain.invoke({
                "question": prompt,
                "chat_history": chain_history,
                "system_prompt": system_prompt,
                "assistant_prompt": assistant_prompt
            })
            return response["answer"][:MAX_TOKENS]
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": assistant_prompt}
            ]
            
            recent_history = conversation_history[-MAX_HISTORY:]
            messages.extend(recent_history)
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=MAX_TOKENS
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"