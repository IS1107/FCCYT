from typing import List, Optional

from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models import Post, Vote
from app.schemas import PostCreateSchema, PostSchema
from app.oauth2 import get_current_user
from app.database import get_db

router = APIRouter(prefix='/posts', tags=['Posts'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=PostSchema)
def create_post(post: PostCreateSchema, db: Session = Depends(get_db),
                current_user: int = Depends(get_current_user)):
    new_post = Post(owner_id=current_user.id, **post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[PostSchema])
def get_all_posts(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: Optional[str] = ''):
    search = f"%{search}%"
    results = db.query(Post, func.count(Vote.post_id).label('votes')).join(Vote, Vote.post_id == Post.id, isouter=True).filter(
        Post.title.ilike(search)).group_by(Post.id).offset(skip).limit(limit).all()

    posts = []
    for post, vote in results:
        post_data = PostSchema.from_orm(post)
        post_data.votes = vote
        posts.append(post_data)
    return posts


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=PostSchema)
def get_pots_by_id(post_id: int, db: Session = Depends(get_db)):
    result = db.query(Post, func.count(Vote.post_id).label('votes')) \
        .join(Vote, Vote.post_id == Post.id, isouter=True) \
        .filter(Post.id == post_id) \
        .group_by(Post.id) \
        .first()

    if result:
        post, votes = result
        post_data = PostSchema.from_orm(post)
        post_data.votes = votes  # Assigning the votes count
        return post_data
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@router.delete('/{id}', status_code=status.HTTP_200_OK)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")

    db.delete(post)
    db.commit()

    return {'message': f'Post deleted'}


@router.patch('/{id}', status_code=status.HTTP_200_OK)
def update_post(post_id: int, post: PostCreateSchema, db: Session = Depends(get_db),
                current_user: int = Depends(get_current_user)):
    updated_post = db.query(Post).filter(Post.id == post_id).first()

    if not updated_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")

    post_data = post.model_dump(exclude_unset=True)
    for key, value in post_data.items():
        setattr(updated_post, key, value)
        db.add(updated_post)
        db.commit()
        db.refresh(updated_post)

    return updated_post
