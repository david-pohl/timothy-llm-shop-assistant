# shop-assistant

todo: external api, on-click scrape update, "please repeat" right after first prompt, containerization, size handling in clothing inventory, documentation

npm i -s cohere-ai

docker load -i shop/intern-hw-simple-website-docker-image.tar
docker run -p 4000:3000 -t -i sha256:57e8fae48a94b48ed3e1e2a020a6a5d21bfabb9f10b0ab2dc4b4c67ad5904896

docker pull mysql
docker run --name mysql -d \
    -p 3306:3306 \
    -e MYSQL_ROOT_PASSWORD=db \
    --restart unless-stopped \
    mysql
docker restart mysql
docker rm mysql

docker exec -it mysql bash;
mysql -u root -p;
SHOW DATABASES;
USE mysql;
DESCRIBE products;
DESCRIBE sizes;
DESCRIBE categories;


docker pull ollama/ollama
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama list
docker exec -it ollama ollama pull llama3.2:3b
docker exec -it ollama ollama run llama3.2:3b

tempdavid: docker stop mysql
tempdavid: docker rm mysql

npm run build
npm run start

to improve:
vector database to catch typos and other problems
optimize prompts, e.g., using dspy
gpu-supported llm
more agent-like behavior (show a picture, then retrieve link or propose alternatives)
improving handling questions regarding prior context
improving caching
fine-tuning the sql retrieval
sizing comparable not string xl > l > m usw.


To test:
1. What's your name?
2. How many jackets are priced under $50?
3. asdasdasd

