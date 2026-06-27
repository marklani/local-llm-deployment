# local-llm-deployment
Project to deploy and host an llm

Follow below steps to start the Ollama server:

1. docker build ./ -t test-pull
2. docker run -d --gpus=all --name gemma4-31b -p 11434:11434 gemma4:31b
3. Run `ollama pull gemma4:31b` in the container to download the model

Ollama server will be running on port 11434 in a container in localhost.

Run `python app.py --model gemma4:31b` in the `web-chatbot` to run the web interface in port `8000`.

Open `localhost:8000` to talk to the chatbot.

# Docker way
Run `docker compose up -d --build` in the `web-chatbot` folder for Windows.
Sometimes the build will fail due to the model runner. Retry until it works.
The memory will persist in the container.