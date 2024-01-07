# Quantum Computing Q/A
## Adoption of D.O.T. (Document Of Things) for Q/A about Quantum Computing in Java

This **Dash** application demonstrates the adoption of the `D.O.T.` framework for Q/A about Quantum Computing in Java
The **Quantum Computing Q/A** is the adoption of `D.O.T.` with the `Chroma` vectorstore created from publicly available Java examples in the `Quantum Computing in Action` [book]( https://www.manning.com/books/quantum-computing-in-action).

![image](https://github.com/gosha70/quantum-chat/assets/17832712/cba513da-af42-4e2c-b392-e121e2db8d78)


_See more details about the D.O.T. framework in [document-assistant repo](https://github.com/gosha70/document-assistant)_

## Running Application

### Running Locally
The LLM model with the vectorstore are already included into the `repo`.

1. Clone this `repo`:
```
git clone git@github.com:gosha70/quantum-chat.git
```   
3. In the directory, where the `repo` was cloned, installed required **Python** libraries:
```
pip3 install -r requirements.txt
```   
4. To the application - just run the following (no input arguments are needed):
```
python3 -m app.chat_app
```

:bookmark: _By default the **Dash** application starts on the port `8050`; if this port is not available on your machine, add `port=YOUR_PORT` in the following call in `chat_app.py`: `app.run_server(debug=False)`._

### Deploy on Render

This application is ready to be deployed on [Render](https://dashboard.render.com/).
