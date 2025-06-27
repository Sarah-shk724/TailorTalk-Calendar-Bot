import streamlit as st
from chat_agent import app as agent
from calendar_api import book_calendar_event
from datetime import datetime

st.set_page_config(page_title="TailorTalk | Sarah Shaikh")
st.title("📅 TailorTalk — Built by Sarah Shaikh")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask me to check your availability or book a meeting")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 👇 Invoke LangGraph and get full response (including slots)
    result = agent.invoke({"user_input": user_input, "next": "", "response": ""})
    st.session_state.messages.append({"role": "assistant", "content": result["response"]})

    # ✅ Add "Book" buttons if free slots were found
    if "slots" in result:
        for idx, slot in enumerate(result["slots"]):
            start, end = slot
            label = f"📅 Book: {datetime.fromisoformat(start).strftime('%I:%M %p')} - {datetime.fromisoformat(end).strftime('%I:%M %p')}"
            if st.button(label, key=f"slot{idx}"):
                event = book_calendar_event("Meeting via TailorTalk", start, end)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Meeting booked! [View event]({event.get('htmlLink')})"
                })

# Show full chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
