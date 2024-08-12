from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Movie, Rating, Comment, User
from app.auth import get_current_user
import logging

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for movie creation
class MovieCreate(BaseModel):
    title: str
    description: str
    release_year: int

# Pydantic model for movie update
class MovieUpdate(BaseModel):
    title: str
    description: str
    release_year: int

# Endpoint to list all movies
@router.get("/", response_model=list[Movie])
def read_movies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        movies = db.query(Movie).offset(skip).limit(limit).all()
        logger.info(f"Fetched {len(movies)} movies.")
        return movies
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to get a movie by ID
@router.get("/{movie_id}", response_model=Movie)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    try:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if movie is None:
            logger.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=404, detail="Movie not found")
        logger.info(f"Fetched movie with ID {movie_id}.")
        return movie
    except Exception as e:
        logger.error(f"Error fetching movie with ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Secure Endpoint to create a new movie
@router.post("/", response_model=Movie)
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_movie = Movie(
            title=movie.title,
            description=movie.description,
            release_year=movie.release_year,
            owner_id=current_user.id  # Ensure Movie model has an 'owner_id' field
        )
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        logger.info(f"Created new movie: {movie.title}")
        return db_movie
    except Exception as e:
        logger.error(f"Error creating movie: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Secure Endpoint to update a movie
@router.put("/{movie_id}", response_model=Movie)
def update_movie(
    movie_id: int,
    movie: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            logger.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=404, detail="Movie not found")
        if db_movie.owner_id != current_user.id:
            logger.warning(f"User {current_user.id} not authorized to update movie with ID {movie_id}.")
            raise HTTPException(status_code=403, detail="Not authorized to update this movie")
        db_movie.title = movie.title
        db_movie.description = movie.description
        db_movie.release_year = movie.release_year
        db.commit()
        db.refresh(db_movie)
        logger.info(f"Updated movie with ID {movie_id}.")
        return db_movie
    except Exception as e:
        logger.error(f"Error updating movie with ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Secure Endpoint to delete a movie
@router.delete("/{movie_id}")
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            logger.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=404, detail="Movie not found")
        if db_movie.owner_id != current_user.id:
            logger.warning(f"User {current_user.id} not authorized to delete movie with ID {movie_id}.")
            raise HTTPException(status_code=403, detail="Not authorized to delete this movie")
        db.delete(db_movie)
        db.commit()
        logger.info(f"Deleted movie with ID {movie_id}.")
        return {"detail": "Movie deleted"}
    except Exception as e:
        logger.error(f"Error deleting movie with ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to rate a movie
@router.post("/{movie_id}/ratings/", response_model=Rating)
def rate_movie(
    movie_id: int,
    rating: int,  # Adjust as needed (could be a Pydantic model)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            logger.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=404, detail="Movie not found")
        db_rating = Rating(
            movie_id=movie_id,
            rating=rating,
            user_id=current_user.id
        )
        db.add(db_rating)
        db.commit()
        db.refresh(db_rating)
        logger.info(f"Added rating for movie ID {movie_id} by user ID {current_user.id}.")
        return db_rating
    except Exception as e:
        logger.error(f"Error adding rating for movie ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to get ratings for a movie
@router.get("/{movie_id}/ratings/", response_model=list[Rating])
def get_movie_ratings(movie_id: int, db: Session = Depends(get_db)):
    try:
        ratings = db.query(Rating).filter(Rating.movie_id == movie_id).all()
        logger.info(f"Fetched {len(ratings)} ratings for movie ID {movie_id}.")
        return ratings
    except Exception as e:
        logger.error(f"Error fetching ratings for movie ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to add a comment to a movie
@router.post("/{movie_id}/comments/", response_model=Comment)
def add_comment(
    movie_id: int,
    comment: str,  # Adjust as needed (could be a Pydantic model)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if db_movie is None:
            logger.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=404, detail="Movie not found")
        db_comment = Comment(
            movie_id=movie_id,
            text=comment,
            user_id=current_user.id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        logger.info(f"Added comment for movie ID {movie_id} by user ID {current_user.id}.")
        return db_comment
    except Exception as e:
        logger.error(f"Error adding comment for movie ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to view comments for a movie
@router.get("/{movie_id}/comments/", response_model=list[Comment])
def get_movie_comments(movie_id: int, db: Session = Depends(get_db)):
    try:
        comments = db.query(Comment).filter(Comment.movie_id == movie_id).all()
        logger.info(f"Fetched {len(comments)} comments for movie ID {movie_id}.")
        return comments
    except Exception as e:
        logger.error(f"Error fetching comments for movie ID {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
