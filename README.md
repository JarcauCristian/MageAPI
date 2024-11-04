# Mage AI API
![Docker Image](https://github.com/JarcauCristian/MageAPI/actions/workflows/docker_image.yml/badge.svg)

Mage AI API tries to automate most of the things that can be done in Mage AI through the power of code.

The API is split in three main categories:
- Pipeline Interactions
- Block Interactions
- Kernel Interactions

To run the API there are two possibilities:
- Locally:
  - Clone the repository: `git clone https://github.com/JarcauCristian/MageAPI.git`
  - Install the requirements: `pip install -r requirements.txt`

- Docker:
  - Getting the official image with: `docker pull ghcr.io/jarcaucristian/mage-api:latest`
    - Setting up the environment variables:
      - **BASE_URL** -> The URL to the Mage AI deployment
      - **EMAIL** -> The email of an account with admin role
      - **PASSWORD** -> The password of an account with admin role
      - **AUTH** -> Can have only two values **[true, false]** if it is false then EMAIL and PASSWORD shouldn't be provided
      - **OLLAMA_URL** -> The URL for an OLLAMA instance
    - Run the image: `docker run -p 8000:8000 -e BASE_URL=<> -e EMAIL=<> -e PASSWORD=<> -e API_KEY=<> ghcr.io/jarcaucristian/mage-api:latest`
  - Build the image: `docker build -t mage_api .`
      - Run the image: `docker run -p 8000:8000 -e BASE_URL=<> -e EMAIL=<> -e PASSWORD=<> -e API_KEY=<> ghcr.io/jarcaucristian/mage-api:latest`
   
Accessing the API swagger documentation at http://localhost:8000/mage/docs
    
