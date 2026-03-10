FROM docker.io/ollama/ollama:rocm
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install sudo -y
EXPOSE 11434
# Pre-Install llama2
RUN nohup bash -c "ollama serve &" && sleep 5 && ollama pull qwen3.5
CMD ["serve"]