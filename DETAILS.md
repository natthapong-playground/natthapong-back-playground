# natthapong-back-playground details

<!-- venv - bash terminal -->
python -m venv venv
source venv/Scripts/activate

<!-- Keep -->
uvicorn app.main:app --reload

<!-- docker -->
touch docker-compose.yml  <!-- create docker-compose -->

docker compose down
docker compose up -d

<!-- Packages -->
pip install "fastapi[standard]" sqlalchemy asyncpg pydantic-settings passlib[bcrypt] pyjwt redis pytest pytest-asyncio httpx

pip freeze > requirements.txt

<!-- 

>>> To handle database, Model in MVC
sqlalchemy - ORM (Object-Relational Mapper), to use python instead of raw SQL
asyncpg - connect with PostgreSQL

>>> To read .env variables
pydantic-settings - core/config file

>>> core/security
passlib[bcrypt] - hashes
pyjwt - creates the expiring OAuth2 session tokens

>>> Session chaching, and load balancer state management
redis

>>> Testing, to simulate network request
pytest
pytest-asyncio
httpx

 -->


