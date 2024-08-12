from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import User
from app.auth import get_current_user
import logging

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserUpdate(BaseModel):
    username: str
    email: str

@router.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"Fetched details for current user with ID {current_user.id}.")
    return current_user

@router.put("/users/me", response_model=User)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Updating details for current user with ID {current_user.id}.")
        current_user.username = user_update.username
        current_user.email = user_update.email
        db.commit()
        db.refresh(current_user)
        logger.info(f"User with ID {current_user.id} updated successfully.")
        return current_user
    except Exception as e:
        logger.error(f"Error updating user with ID {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User with ID {user_id} not found.")
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"Fetched user with ID {user_id}.")
        return user
    except Exception as e:
        logger.error(f"Error fetching user with ID {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
