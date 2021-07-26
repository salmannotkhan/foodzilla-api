from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os

HOST = os.environ['DB_HOST']
USER = 'foodzilla'
PASS = os.environ['DB_PASS']
DB = 'foodzilla'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"Welcome": "Sanjeev kapoor"}


@app.get("/recipes")
def recipes(last_id: int = 0,
            is_veg: bool = None,
            taste: str = None,
            cuisine: str = None,
            course: str = None,
            query: str = None):
    params = []
    sql = """SELECT ARRAY(SELECT ROW_TO_JSON(R.*) AS json
            FROM (SELECT id, name, is_veg, image from recipe) R,
            (SELECT * FROM recipe) recipe WHERE"""
    if is_veg is not None:
        params.append(is_veg)
        sql += ' recipe.is_veg = %s AND'
    if query is not None:
        params.append("%"+query.lower()+"%")
        sql += ' LOWER(recipe.name) LIKE %s AND'
    if taste is not None:
        params.append(tuple(taste.split("|")))
        sql += ' recipe.taste IN %s AND'
    if course is not None:
        params.append(tuple(course.split("|")))
        sql += ' recipe.course IN %s AND'
    if cuisine is not None:
        params.append(tuple(cuisine.split("|")))
        sql += ' recipe.cuisine IN %s AND'
    con = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASS)
    sql += ' recipe.id = R.id AND'
    sql += ' recipe.id > %s ORDER BY recipe.id LIMIT 10)'
    params.append(last_id)
    with con.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchone()[0]

    return rows


@app.get("/recipe/{id}")
def recipe(id: int):
    con = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASS)
    sql = 'SELECT JSON_AGG(RECIPE.*)AS json FROM RECIPE WHERE id = %s'

    with con.cursor() as cur:
        cur.execute(sql, [id])
        row = cur.fetchone()[0][0]

    return row


@app.get("/recipe/{id}/ratings")
def ratings(id: int):
    con = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASS)
    sql = """SELECT ARRAY(SELECT JSON_AGG(ratings.*)
            FROM ratings WHERE recipe_id= %s)"""
    with con.cursor() as cur:
        cur.execute(sql, [id])
        row = cur.fetchone()

    return row[0][0]


@app.post("/recipe/{id}/rate")
def rate(email: str, recipe_id: int, star: int, review: str):
    if star > 5 or star < 1:
        return {"success": False,
                "error": "Invalid Rating"}
    con = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASS)
    sql = """INSERT INTO ratings (email, recipe_id, star, review)
            VALUES(%s, %s, %s, %s)"""

    with con.cursor() as cur:
        cur.execute(sql, [email, recipe_id, star, review])
        con.commit()

    return {"success": True,
            "error": None}
