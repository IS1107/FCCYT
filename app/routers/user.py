from typing import List

from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session

from app.models import User
from app.oauth2 import get_current_user
from app.schemas import UserCreateSchema, UserOutSchema, UserUpdateSchema
from app.utils import hash_p

from app.database import get_db

router = APIRouter(prefix='/users', tags=['Users'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserOutSchema)
def create_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    # hash the password - user.password
    hashed_password = hash_p(user.password)
    user.password = hashed_password
    new_user = User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[UserOutSchema])
def get_users(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    return db.query(User).all()


@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserOutSchema)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete('/{user_id}', status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.patch('/{user_id}', status_code=status.HTTP_200_OK)
def update_user(user_id: int, user: UserUpdateSchema, db: Session = Depends(get_db),
                current_user: int = Depends(get_current_user)):
    user_update = db.query(User).filter(User.id == user_id).first()

    if not user_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")

    user_data = user.model_dump(exclude_unset=True)
    for key, value in user_data.items():
        setattr(user_update, key, value)
    db.add(user_update)
    db.commit()
    db.refresh(user_update)
    return user_update
