# local-llm-deployment
Project to deploy and host an llm

Follow below steps to start the Ollama server:

1. docker build ./ -t qwen3.5:4b
2. docker run -d --gpus=all --name qwen3.5:4b -p 11434:11434 qwen3.5:4b

Ollama server will be running on port 11434 in a container in localhost.

Run `python app.py --model qwen3.5:4b` in the `web-chatbot` to run the web interface in port `8000`.

Open `localhost:8000` to talk to the chatbot.

The chatbot currently does not remember context of previous chats.