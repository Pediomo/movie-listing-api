from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel
from app.database import SessionLocal, init_db
from app.models import Movie, User, Rating, Comment
from auth import SECRET_KEY, ALGORITHM
from auth import router as auth_router
import logging
from fastapi.responses import JSONResponse

app = FastAPI()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Pydantic models for request validation
class MovieCreate(BaseModel):
    title: str
    description: str
    release_year: int

class RatingCreate(BaseModel):
    movie_id: int
    rating: int  # 1 to 5

class CommentCreate(BaseModel):
    movie_id: int
    text: str
    parent_id: int = None  # For nested comments

# Middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Endpoint to list all movies
@app.get("/movies/")
def read_movies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Fetching all movies")
    movies = db.query(Movie).offset(skip).limit(limit).all()
    return movies

# Endpoint to get a movie by ID
@app.get("/movies/{movie_id}")
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie is None:
        logger.warning(f"Movie with ID {movie_id} not found")
        raise HTTPException(status_code=404, detail="Movie not found")
    logger.info(f"Fetching movie with ID {movie_id}")
    return movie

# Secure Endpoint to create a new movie
@app.post("/movies/")
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} is creating a new movie: {movie.title}")
    db_movie = Movie(
        title=movie.title,
        description=movie.description,
        release_year=movie.release_year,
        owner_id=current_user.id  # Ensure Movie model has an 'owner_id' field
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

# Secure Endpoint to update a movie
@app.put("/movies/{movie_id}")
def update_movie(
    movie_id: int,
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if db_movie is None:
        logger.warning(f"Movie with ID {movie_id} not found for update")
        raise HTTPException(status_code=404, detail="Movie not found")
    if db_movie.owner_id != current_user.id:
        logger.warning(f"Unauthorized update attempt by user {current_user.username} on movie ID {movie_id}")
        raise HTTPException(status_code=403, detail="Not authorized to update this movie")
    db_movie.title = movie.title
    db_movie.description = movie.description
    db_movie.release_year = movie.release_year
    db.commit()
    db.refresh(db_movie)
    logger.info(f"Movie with ID {movie_id} updated by user {current_user.username}")
    return db_movie

# Secure Endpoint to delete a movie
@app.delete("/movies/{movie_id}")
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if db_movie is None:
        logger.warning(f"Movie with ID {movie_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Movie not found")
    if db_movie.owner_id != current_user.id:
        logger.warning(f"Unauthorized delete attempt by user {current_user.username} on movie ID {movie_id}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this movie")
    db.delete(db_movie)
    db.commit()
    logger.info(f"Movie with ID {movie_id} deleted by user {current_user.username}")
    return {"detail": "Movie deleted"}

# Endpoint to rate a movie
@app.post("/ratings/")
def rate_movie(
    rating: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} is rating movie ID {rating.movie_id} with rating {rating.rating}")
    db_rating = Rating(
        movie_id=rating.movie_id,
        rating=rating.rating,
        user_id=current_user.id
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

# Endpoint to get ratings for a movie
@app.get("/movies/{movie_id}/ratings/")
def get_movie_ratings(movie_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching ratings for movie ID {movie_id}")
    ratings = db.query(Rating).filter(Rating.movie_id == movie_id).all()
    return ratings

# Endpoint to add a comment to a movie
@app.post("/comments/")
def add_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} is adding a comment to movie ID {comment.movie_id}")
    db_comment = Comment(
        movie_id=comment.movie_id,
        text=comment.text,
        user_id=current_user.id,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# Endpoint to view comments for a movie
@app.get("/movies/{movie_id}/comments/")
def get_movie_comments(movie_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching comments for movie ID {movie_id}")
    comments = db.query(Comment).filter(Comment.movie_id == movie_id).all()
    return comments

@app.get("/", tags=["root"])
async def read_root():
    """
    Root endpoint to check if the server is running.
    """
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Movie Listing API. Use /docs or /redoc for API documentation."}

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic exception handler for unexpected errors.
    """
    logger.error(f"An unexpected error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/auth")
