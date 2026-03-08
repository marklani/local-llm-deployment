# local-llm-deployment
Project to deploy and host an llm

Follow below steps to start the Ollama server:

1. docker build ./ -t local-llm-deployment-image
2. docker run -d --name ollama3 -p 11434:11434 localhost/local-llm-deployment-image

Ollama server will be running on port 11434 in a container in localhost.

Run `python app.py` in the `web-chatbot` to run the web interface in port `8000`.

Open `localhost:8000` to talk to the chatbot.