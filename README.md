

# **Movie Listing API**

## **Overview**

This is a **Movie Listing API** built with **FastAPI**, allowing users to view, add, edit, and delete movies, as well as rate and comment on them. It uses **JWT** for authentication and supports nested comments.

## **Features**

- **User Authentication**
  - Register a new user
  - Log in with an existing user
  - JWT token-based authentication

- **Movie Management**
  - View all movies
  - View a specific movie by ID
  - Add a new movie
  - Edit a movie (only by the user who added it)
  - Delete a movie (only by the user who added it)

- **Rating System**
  - Rate a movie
  - View ratings for a movie

- **Comments**
  - Add comments to movies
  - View comments for a movie
  - Add nested comments to other comments

## **Requirements**

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite (or other SQL databases)
- Passlib
- PyJWT
