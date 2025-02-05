#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import os
from flask_cors import CORS


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# Route 1: GET /restaurants
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in restaurants])


# Route 2: GET /restaurants/<int:id>
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404

    # Getting associated restaurant_pizzas
    restaurant_pizzas = []
    for rp in restaurant.pizzas:
        restaurant_pizzas.append({
            "id": rp.id,
            "pizza": rp.pizza.to_dict(only=('id', 'name', 'ingredients')),
            "pizza_id": rp.pizza_id,
            "price": rp.price,
            "restaurant_id": rp.restaurant_id
        })

    return jsonify({
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "restaurant_pizzas": restaurant_pizzas
    })


# Route 3: DELETE /restaurants/<int:id>
@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404

    # Delete associated restaurant_pizzas first if cascade isn't set
    for rp in restaurant.pizzas:
        db.session.delete(rp)

    # Now delete the restaurant
    db.session.delete(restaurant)
    db.session.commit()

    return '', 204


# Route 4: GET /pizzas
@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in pizzas])


# Route 5: POST /restaurant_pizzas
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    # Validate input
    if price < 1 or price > 30:
        return jsonify({"errors": ["Price must be between 1 and 30"]}), 400

    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not pizza or not restaurant:
        return jsonify({"errors": ["Invalid pizza_id or restaurant_id"]}), 400

    # Create the new RestaurantPizza
    restaurant_pizza = RestaurantPizza(
        price=price,
        pizza_id=pizza_id,
        restaurant_id=restaurant_id
    )

    db.session.add(restaurant_pizza)
    db.session.commit()

    # Send the response with the new restaurant pizza data
    return jsonify({
        "id": restaurant_pizza.id,
        "pizza": pizza.to_dict(only=('id', 'name', 'ingredients')),
        "pizza_id": pizza.id,
        "price": restaurant_pizza.price,
        "restaurant": restaurant.to_dict(only=('id', 'name', 'address')),
        "restaurant_id": restaurant.id
    }), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
