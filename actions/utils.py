import secrets
import random

# ENUMERATOR
TYPE_VEGAN = "Vegan"
TYPE_VEGETARIAN = "Vegetarian"
TYPE_SPICY = "Spicy"


# print out messages
is_debug = False
def debug(msg):
    if is_debug:
        print('#############')
        print(str(msg))
        print('#############')


# returns the items list in format " COUNT ITEM_NAME, COUNT ITEM_NAME, ... "
def get_order_items_string(items):
    order = {}
    # count the items
    for item in items:
        if item in order.keys():
            order[item] += 1
        else:
            order[item] = 1 

    return ", ".join([f"{count} {name}" for name, count in order.items()])


def generate_order_id():
    return secrets.token_urlsafe(12)


class Pizza:
    def __init__(self, name, ingredients, price, typology):
        self.name = name
        self.ingredients = ingredients
        self.price = price
        self.typology = typology

class Drink:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Store:
    def __init__(self, name, pizzas, drinks, telephone):
        self.name = name
        self.pizzas = pizzas
        self.drinks = drinks
        self.telephone = telephone
    
    def get_pizzas(self):
        return list(self.pizzas.keys())
    
    def get_drinks(self):
        return list(self.drinks.keys())
        
    def get_pizza_ingredients(self, pizza_name):
        return ", ".join(self.pizzas[pizza_name].ingredients) if pizza_name in self.get_pizzas() else None
        
    def get_item_price(self, item_name):
        if item_name in self.get_pizzas():
            return self.pizzas[item_name].price
        elif item_name in self.get_drinks():
            return self.drinks[item_name].price
        else:
            return None
    
    def get_total_price(self, items):
        total_price = 0
        total_price += sum([self.get_item_price(item_name) for item_name in items])
        return total_price



# mock function to retrieve the status of the order
def get_order_status(order):
    return random.choice(['in the queue', 'being prepared', 'in the oven', 'getting ready for delivering', 'on the road', 'delivered'])


# function to initialize available stores, pizzas and drinks
def get_stores():
    # PIZZAS
    margherita = Pizza("Margherita", ["Tomato sauce", "Mozzarella"], 6.50, TYPE_VEGETARIAN)
    hawaii = Pizza("Hawaii", ["Tomato sauce", "Mozzarella", "Pineapple", "Ham"], 8.00, None)
    ham_and_mushrooms = Pizza("Ham and mushrooms", ["Tomato sauce", "Mozzarella", "Ham", "Mushrooms"], 7.50, None)
    pepperoni = Pizza("Pepperoni", ["Tomato sauce", "Mozzarella", "Pepperoni"], 7.00, TYPE_SPICY)
    four_cheese = Pizza("4 Cheese", ["Tomato sauce", "Mozzarella", "Parmesan", "Cheddar", "Green cheese"], 8.50, TYPE_VEGETARIAN)
    veggie = Pizza("Veggie", ["Tomato sauce", "Vegan cheese"], 7.00, TYPE_VEGAN)
    tuna = Pizza("Tuna", ["Tomato sauce", "Mozzarella", "Tuna"], 7.00, None)
    tuna_and_onion = Pizza("Tuna and onion", ["Tomato sauce", "Mozzarella", "Tuna", "Onion"], 7.50, None)
    mexican = Pizza("Mexican", ["Tomato sauce", "Mozzarella", "Pepperoni", "Jalapenos"], 7.50, TYPE_SPICY)
    meat = Pizza("Meat", ["Tomato sauce", "Mozzarella", "Pepperoni", "Italian sausage"], 8.50, TYPE_SPICY)
    chicken = Pizza("Chicken", ["Tomato sauce", "Mozzarella", "Chicken breast"], 7.50, None)
    supreme = Pizza("Supreme", ["Tomato sauce", "Mozzarella", "Pepperoni", "Bacon", "Mushrooms", "Ham"], 9.50, TYPE_SPICY)
    spicy_buffalo = Pizza("Spicy Buffalo", ["Tomato sauce", "Mozzarella", "Chicken breast", "Spicy buffalo sauce"], 8.50, TYPE_SPICY)
    american = Pizza("American", ["Tomato sauce", "Mozzarella", "Pepperoni", "Mushrooms"], 8.00, TYPE_SPICY)
    dominos_pizzas = {
        "Margherita" : margherita,
        "Hawaii" : hawaii,
        "Ham and mushrooms" : ham_and_mushrooms,
        "Pepperoni" : pepperoni,
        "4 Cheese" : four_cheese,
        "Veggie" : veggie,
        "Tuna" : tuna,
        "Tuna and onion" : tuna_and_onion,
        "Mexican" : mexican
    }
    pizzahut_pizzas = {
        "Margherita" : margherita,
        "Hawaii" : hawaii,
        "Ham and mushrooms" : ham_and_mushrooms,
        "Pepperoni" : pepperoni,
        "Meat" : meat,
        "Chicken" : chicken,
        "Supreme" : supreme
    }
    papajohns_pizzas = {
        "Margherita" : margherita,
        "Hawaii" : hawaii,
        "Ham and mushrooms" : ham_and_mushrooms,
        "Pepperoni" : pepperoni,
        "4 Cheese" : four_cheese,
        "Tuna" : tuna,
        "Chicken" : chicken,
        "Spicy Buffalo" : spicy_buffalo,
        "American" : american
    }
    # DRINKS
    coke = Drink("1 liter coke", 3.00)
    water = Drink("1 liter water", 2.00)
    beer = Drink("Half liter beer", 2.00)
    drinks = {
        "1 liter coke" : coke,
        "1 liter water" : water,
        "Half liter beer" : beer
    }
    # STORES
    dominos = Store("Domino's", dominos_pizzas, drinks, "+39 045 464 2310")
    pizzahut = Store("Pizza Hut", pizzahut_pizzas, drinks, "+33 493 824 575")
    papajohn = Store("Papa John's", papajohns_pizzas, drinks, "+357 77 775 252")

    return {
        "Domino's" : dominos,
        "Pizza Hut" : pizzahut,
        "Papa John's" : papajohn
    }


# mock class to retrieve shops infos
class PizzaStoreHelper:
    stores = get_stores()

    def search(self):
        return self.stores.keys()
    
    def get_pizzas(self, store_name):
        return self.stores[store_name].get_pizzas()

    def get_drinks(self, store_name):
        return self.stores[store_name].get_drinks()
    
    def get_telephone(self, store_name):
        return self.stores[store_name].telephone
    
    def get_pizza_ingredients(self, store_name, pizza_name):
        return self.stores[store_name].get_pizza_ingredients(pizza_name)
    
    def get_item_price(self, store_name, item_name):
        return self.stores[store_name].get_item_price(item_name)
    
    def get_total_price(self, store_name, items):
        return self.stores[store_name].get_total_price(items)

    # return the list of pizzas that can be ordered and the ones not availables
    def filter_pizza_choice(self, store_name, pizzas):
        availables = []
        not_availables = []
        menu = self.get_pizzas(store_name) + self.get_drinks(store_name)

        for pizza in pizzas:
            if pizza in menu:
                availables.append(pizza)
            else:
                not_availables.append(pizza)

        return availables, list(set(not_availables))

    # return the list of filtered by type pizzas
    def get_filtered_pizzas(self, store_name, typology):
        availables = []
        menu = self.stores[store_name].pizzas

        for pizza_name, pizza in menu.items():
            if pizza.typology == typology or (typology == TYPE_VEGETARIAN and pizza.typology == TYPE_VEGAN):
                availables.append(pizza_name)

        return availables

