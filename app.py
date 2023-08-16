import time
import os
import openai
import streamlit as st
from PyPDF2 import PdfReader

API_KEY = os.environ["OPENAI_KEY"]
openai.api_key = API_KEY
temperature = 0
model_id = "gpt-3.5-turbo-16k"

def estimate_tokens(text, method="max"):
  # method can be "average", "words", "chars", "max", "min", defaults to "max"
  # "average" is the average of words and chars
  # "words" is the word count divided by 0.75
  # "chars" is the char count divided by 4
  # "max" is the max of word and char
  # "min" is the min of word and char
  word_count = len(text.split(" "))
  char_count = len(text)
  tokens_count_word_est = round(word_count/0.75)
  tokens_count_char_est = round(char_count/4)
  output = 0
  if method == "average":
    output = (tokens_count_word_est + tokens_count_char_est) / 2
  elif method == "words":
    output = tokens_count_word_est
  elif method == "chars":
    output = tokens_count_char_est
  elif method == 'max':
    output = max(tokens_count_word_est,tokens_count_char_est)
  elif method == 'min':
    output = min(tokens_count_word_est,tokens_count_char_est)
  else:
    # return invalid method message
    return "Invalid method. Use 'average', 'words', 'chars', 'max', or 'min'."
  return output

def chatgpt_conversation(conversation_log):
  response = openai.ChatCompletion.create(
    model = model_id,
    temperature = temperature,
    messages = conversation_log
  )
  conversation_log.append({
    'role': response.choices[0].message.role,
    'content': response.choices[0].message.content.strip()
  })
  return conversation_log

st.write("**DocuBlend** Beta : AI-Powered Document Blender by **Sherwood Analytica**")

instruction1_template = "You are my reading assistant. You will read the text I provide and summarize into bullet points. Identify the main ideas and key details in the text, and condense them into concise bullet points. Recognize the overall structure of the text and create bullet points that reflect this structure. The output should be presented in a clear and organized way. Do not start with any titles."
instruction2_template = "You are my writing assistant. Synthesize an article from the bullet points I provide."

instruction1 = st.text_area("**Enter** the 1st instruction to extract from each article.", value = instruction1_template)
instruction2 = st.text_area("**Enter** the 2nd instruction to blend all of the articles.", value = instruction2_template)

uploaded_files = st.file_uploader("**Upload** the PDF documents you would like me to blend for you. My length limit is around 10,000 words per document.", type = "pdf", accept_multiple_files = True)
total_output = ""
for uploaded_file in uploaded_files:
  raw_text = ""
  doc_reader = PdfReader(uploaded_file)
  for i, page in enumerate(doc_reader.pages):
    if estimate_tokens(raw_text, method="max") > 14337: 
      st.write("WARNING: Input length exceeds token limit. Input will be truncated.")
      break
    text = page.extract_text()
    raw_text = raw_text + text + "\n"
  
  start = time.time()
  conversations = []
  conversations.append({'role': 'system', 'content': instruction1})
  conversations.append({'role': 'user', 'content': raw_text})
  conversations = chatgpt_conversation(conversations)
  output_text = conversations[-1]['content']
  #st.write(uploaded_file.name)
  #st.write(output_text)
  end = time.time()
  st.write(uploaded_file.name + " (" + str(round(end-start,2)) + " seconds)")
  total_output = total_output + output_text + "\n\n"

if total_output != "":
  start = time.time()
  conversations = []
  conversations.append({'role': 'system', 'content': instruction2})
  conversations.append({'role': 'user', 'content': instruction2 + ":\n\n" + total_output})
  conversations = chatgpt_conversation(conversations)
  article = conversations[-1]['content']
  end = time.time()
  st.write("**Blended Article** + " (" + str(round(end-start,2)) + " seconds)")
  st.write(article)
  st.divider()
  st.download_button(":scroll:", article)
