from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException