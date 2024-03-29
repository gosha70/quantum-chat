import logging
import json
import time
import dash
from datetime import datetime
from dash import html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from retrieval_constants import CURRENT_DIRECTORY
from models.model_info import ModelInfo
from embeddings.embedding_database import load_vector_store
from retrieval_qa import create_retrieval_qa
from prompt_info import PromptInfo

QC_SYSTEM_PROMPT = """As an assistant powered by a language learning model, 
your primary role is to assist Java developers by answering their questions about Quantum Computing and how to use org.redfx 
Java API using the context provided to you. 
It's essential to thoroughly read and understand the given context and/or Java code before attempting to respond to queries. 
Approach each question methodically, breaking down the process into clear, logical steps. 
If a user's question falls outside the scope of the provided context and you're unable 
to answer based on the information at hand, be honest and inform the user that you cannot provide an answer. 
Avoid using external or additional information that is not part of the given context. 
Strive to provide comprehensive and detailed answers to all questions, ensuring clarity and helpfulness in your responses."""

DB_FOLDER = 'quantumjava_doc_db' 
DB_COLLECTION_NAME= "EGOGE_DOCUMENTS_DB"

with open('app_config.json', 'r') as file:
    app_config = json.load(file)

verbose = False
qa_service = None
next_question_delay = app_config["next_question_delay"]
# The number of seconds passed b/w questions
if next_question_delay is None or next_question_delay < 1:
    next_question_delay = 1
print(f"Minimum wait in seconds b/w questions: {next_question_delay}")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
#app.config.suppress_callback_exceptions = True

SYSTEM_ERROR = "I apologize, but I'm unable to provide a specific answer to your question based on the information currently available to me.\nMy ability to respond accurately depends on a variety of factors, including the scope of my training data and the specific details of your query.\nIf you have any other questions or need assistance with a different topic, please feel free to ask, and I'll do my best to help."

# Set the logging level to INFO    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

verbose = False

model_info = ModelInfo() # DEFAULT_MODEL_NAME = "hkunlp/instructor-large"

prompt_info = PromptInfo(QC_SYSTEM_PROMPT, None, True)

logging.info(f"Loading the vectorstore from {DB_FOLDER} ...")
docs_db = load_vector_store(
    model_name=model_info.model_name, 
    collection_name=DB_COLLECTION_NAME, 
    persist_directory=DB_FOLDER
)
if docs_db is None:
    logging.error(f"Failed to load the vectorstore from {DB_FOLDER}.")  
else:
    dic = docs_db.get()["ids"]
    logging.info(f"Loaded the vectorstore with {len(dic)} documents.")  
    qa_service = create_retrieval_qa(model_info=model_info, prompt_info=prompt_info, vectorstore=docs_db)
    
# This layout closely follows the structure of popular chat applications
app.layout = dbc.Container([
        html.Div([
            html.Div([  # Div for image and text
                html.Img(src=app_config["chat_logo"], className='title-image'),  # Custom Image
                html.Div([  # Nested Div for title and subtitle
                        html.Span(app_config["chat_title"], className='title-span'),  # Title text
                        html.Span(app_config["chat_subtitle"], className='subtitle-span')  # Subtitle text
                ], style={'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '10px'})  
            ], style={'textAlign': 'left', 'color': '#E4E4E7', 'display': 'flex', 'alignItems': 'center'})
        ], className='header-container'),

        html.Hr(className="chat-bottom-hr"),   

        # Pevents the concurrent request to LLM
        dcc.Store(id='click-store', data={'last_click_time': 0}),

        dbc.Row(
            dbc.Col(
                html.Div(id='chat-box-id', className='chat-box chat-box-hidden'),
                width=12,
            ),
            className="mb-2"
        ),

        html.Hr(className="chat-top-hr"),     

        dbc.Row(
            [
                dbc.Col(
                    dcc.Textarea(
                        id='message-input-id', 
                        placeholder=app_config["chat_ask_placeholder"], 
                        className='message-input',
                        disabled=False
                    ),
                    width=10,
                ),
                dbc.Col(
                    dbc.Button(
                        html.Img(src=app_config["ask_button"], className='ask-button-img'), 
                        id='ask-button-id', 
                        n_clicks=0,
                        className="mb-2 ask-button", 
                        disabled=False
                    ),
                    width=2,
                )
            ]
        ),
        
        html.P(
            app_config["copyright"],
            className="custom-footer-style"
        )
    ],
    fluid=True,
    className='container-style' 
)


def formatted_datetime():
    # Format the date and time to display in the chat to: 'Dec 25, 2023 12:00 PM'
    return datetime.now().strftime('%b %d, %Y %I:%M %p')


def check_get_click_time(n_clicks, data):    
    current_time = time.time()
    # Get the last click time from the store
    last_click_time = data['last_click_time']    
    if last_click_time is None:
        return current_time
        
    # Calculate the time since the last click
    time_since_last_click = current_time - last_click_time 
    if n_clicks is None or time_since_last_click <= next_question_delay:
        raise PreventUpdate
    
    return current_time


@app.callback(
    [Output('click-store', 'data'),
     Output('message-input-id', 'value', allow_duplicate=True),
     Output('message-input-id', 'disabled', allow_duplicate=True),
     Output('ask-button-id', 'disabled', allow_duplicate=True)],
    [Input('ask-button-id', 'n_clicks')],
    [State('click-store', 'data')],
    prevent_initial_call=True
)
def update_click_store(n_clicks, data):
    data['last_click_time'] = check_get_click_time(n_clicks, data)
    return data, app_config["wait_info"], True, True


@app.callback(
    [Output('chat-box-id', 'children'),
     Output('chat-box-id', 'className'),
     Output('message-input-id', 'value'),
     Output('message-input-id', 'disabled'),
     Output('ask-button-id', 'disabled')],
    [Input('ask-button-id', 'n_clicks')],
    [State('message-input-id', 'value'),
     State('chat-box-id', 'children'),
     State('click-store', 'data')]
)
def update_chat(n_clicks, message, chat_elements, data):   
    if message is None:
        raise PreventUpdate   
    
    data['last_click_time'] = check_get_click_time(n_clicks, data)
    # Disable the button at the start
    chat_elements = chat_elements or []
    try:
        user_icon = app_config["user_icon"]
        system_icon = app_config["system_icon"]
        system_error_icon = app_config["system_error_icon"]

        question_div = html.Div(
            [
                html.Div(
                    [
                        html.Img(src=user_icon, className="chat-icon user-icon"),
                        html.Span(formatted_datetime(), className="chat-datetime") 
                    ],
                    className="chat-header"
                ),
                html.P(message, className="chat-message user-message")
            ],
            className="chat-bubble user-bubble"
        )

        try:
            answer = get_answer(message)  # Placeholder for your answer generation logic
            answer_div = html.Div(
                [                    
                    html.Div( 
                        [
                            html.Img(src=system_icon, className="chat-icon system-icon"),
                            html.Span(formatted_datetime(), className="chat-datetime") 
                        ],
                        className="chat-header"
                    ),
                    # html.P(answer, className="chat-message system-message")
                    dcc.Markdown(answer.replace('\n', '\n\n'), className="chat-message system-message")
                ],
                className="chat-bubble system-bubble"
            )
        except Exception as error:
            logging.error(f"Failed to answer on the question: '{message}'.\nError: {str(error)}", exc_info=True)
            answer_div = html.Div(
                [
                    html.Img(src=system_error_icon, className="chat-icon system-icon"),
                    html.P(SYSTEM_ERROR, className="chat-message system-error-message")
                ],
                className="chat-bubble system-bubble"
            )
        
        chat_elements.extend([question_div, answer_div])
    except Exception as error:     
        logging.error(f"Failed to process the messsage: '{message}'.\nError: {str(error)}", exc_info=True)

    return chat_elements, 'chat-box-shown', '', False, False


# Placeholder function for generating system answers
def get_answer(question):
    # Get the answer from the chain
    logging.info(f"Asking the question:\n {question}")  
    results = qa_service(question)
    answer, docs = results["result"], results["source_documents"]
    logging.info(f"Got the answer on the question:\n {question}.") 
    if verbose: 
        log_message = f"=============\n{answer}\n"
        for document in docs:
            log_message = log_message +  f">>> {document.metadata['source']}:{document.page_content}\n"
        log_message = log_message + "=============" 
        logging.info(log_message)
    
    return answer

if __name__ == '__main__':  
    if qa_service is None:
        logging.error(f"Failed to initialize the retrieval framework for the vectorstore located in {DB_FOLDER}.")  
    else:    
        app.run_server(debug=False)   
        
