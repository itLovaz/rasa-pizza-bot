# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import time
import secrets
import random
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, UserUtteranceReverted


is_debug = True
def debug(msg):
    if is_debug:
        print('#############')
        print(str(msg))
        print('#############')

def get_order_pizzas_string(pizzas):
    order = {}
    # count the pizzas
    for pizza in pizzas:
        if pizza in order.keys():
            order[pizza] += 1
        else:
            order[pizza] = 1 

    return ", ".join([f"{count} {name}" for name, count in order.items()])



# mock class to retrieve shops and infos
class PizzaStoreHelper:
    stores = {}
    dominos_menu = ["Margherita", "Hawaii", "4 Cheese", "Tuna", "Tuna and onion", "Veggie", "Pepperoni", "Mexican", "Ham and mushrooms"]
    pizzahut_menu = ["Margherita", "Hawaii", "Meat", "Chicken", "Supreme", "Pepperoni", "Ham and mushrooms"]
    papajohn_menu = ["Margherita", "Tuna", "Hawaii", "Spicy Buffalo", "American", "Chicken", "Pepperoni", "Ham and mushrooms", "4 Cheese"]

    def __init__(self, n_stores=3):
        self.stores = {1:"Domino's", 2:"Pizza Hut", 3:"Papa John's"}
    def search(self):
        return self.stores
    
    def get_menu(self, store_name):
        if store_name.lower() == "domino's":
            return self.dominos_menu
        elif store_name.lower() == "pizza hut":
            return self.pizzahut_menu
        elif store_name.lower() == "papa john's":
            return self.papajohn_menu
    
    def get_store_number(self, store_name):
        if store_name.lower() == "domino's":
            return "+39 045 464 2310"
        elif store_name.lower() == "pizza hut":
            return "+33 493 824 575"
        elif store_name.lower() == "papa john's":
            return "+357 77 775 252"

    # return the list of pizzas that can be ordered and the ones not availables
    def filter_pizza_choice(self, store, pizzas):
        availables = []
        not_availables = []
        menu = self.get_menu(store)

        for pizza in pizzas:
            if pizza in menu:
                availables.append(pizza)
            else:
                not_availables.append(pizza)

        return availables, list(set(not_availables))


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return 'action_default_fallback'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        

        output = [UserUtteranceReverted()]
        
        # dispatcher.utter_message(response="utter_ask_rephrase")
        # current_step = tracker.get_slot('current_step')
        # debug(f'CURRENT STEP "{current_step}"')

        # if current_step is not None:
        #     if tracker.latest_message['intent'].get('name') == 'need_explanation':
        #         print(f'{current_step}_explain')
        #         dispatcher.utter_message(response=f'{current_step}_explain')

        #     if current_step[0:6] == 'action':
        #         debug('ACTION')
        #         output.append(FollowupAction(current_step))
        #     elif current_step[0:5] == 'utter':
        #         debug('MESSAGE')
        #         # related_intent = get_previous_latest_message_intent(tracker.latest_message)
        #         # print(related_intent)
        #         # print(get_current_step_related_intent(current_step))
        #         # if related_intent != get_current_step_related_intent(current_step):
        #         #     dispatcher.utter_message(response=f'{current_step}_explain')                
        #         # dispatcher.utter_message(response=current_step)

        return output

class ActionExplain(Action):
    def name(self) -> Text:
        return 'action_explain'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_step = tracker.get_slot('current_step')
        response = 'utter_out_of_scope'

        if current_step is not None and (current_step == 'utter_ask_address' or current_step == 'utter_ask_time' or current_step == 'utter_ask_telephone'):
            dispatcher.utter_message(response=f'{current_step}_explain')
            
        dispatcher.utter_message(response=response)

        return []


class ActionChooseStore(Action):
    # texts = None
    psf = None
    def __init__(self):
        # self.texts = Texts()
        self.psf = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_choose_store"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_choose_store_searching')
        stores = self.psf.search()
        if len(stores) == 0:
            dispatcher.utter_message(response='utter_choose_store_found_none')
        elif len(stores) == 1:
            dispatcher.utter_message(response='utter_choose_store_found_one', store=next(iter(stores.values())))
        else:
            dispatcher.utter_message(response='utter_choose_store_found')
            for index,name in stores.items():
                dispatcher.utter_message(response='utter_single_element', element=name)
            dispatcher.utter_message(response='utter_ask_store')

        debug("Stores: " + str(stores))

        # if I change store clean up any left pizza
        return [SlotSet("pizzas", []), SlotSet('current_step', 'action_choose_store')]

class ActionShowMenu(Action):
    psf = None
    def __init__(self):
        self.psf = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_show_menu"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        if store is not None: 
            menu = self.psf.get_menu(store)

            dispatcher.utter_message(response='utter_show_menu_results', store=store)
            for pizza in menu:
                dispatcher.utter_message(response='utter_single_element', element=pizza)
            dispatcher.utter_message(response='utter_ask_new_pizzas', store=store)

            debug("Store: " + str(store))

            return []
        else:
            return [FollowupAction('action_choose_store')]



# adding the choosen pizzas to the list
class actionFixPizzasChoice(Action):
    psf = None
    def __init__(self):
        self.psf = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_fix_pizzas_choice"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        new_pizzas = tracker.get_slot('new_pizzas') 
        curr_pizzas = tracker.get_slot('pizzas') if tracker.get_slot('pizzas') is not None else []


        pizzas_to_add = self.checkForMorePizzas(tracker)
        debug("NEW PIZZAS: " + str(new_pizzas))
        debug("CURR PIZZAS: " + str(curr_pizzas))
        debug("TO ADD PIZZAS: " + str(pizzas_to_add))

        store = tracker.get_slot('store')

        # in case I order multiple pizzas I add them all, otherwise only the one given
        # but i check that the pizzas are available for that store
        availables, not_availables = self.psf.filter_pizza_choice(store, pizzas_to_add if pizzas_to_add else new_pizzas)
        curr_pizzas.extend(availables)
        if not_availables:
            dispatcher.utter_message(text=f"The following pizzas are not available at {store}: {[', '.join(not_availables)]}")
        
        # if no pizzas were added then I should show the menu again
        output = [SlotSet("pizzas", curr_pizzas), SlotSet('current_step', 'action_ask_something_more')]
        if len(curr_pizzas) == 0:
            output = [FollowupAction('action_show_menu')]

        # previous code not involving the filter_pizza
        # curr_pizzas.extend(pizzas_to_add if pizzas_to_add else new_pizzas )

        debug("CURR PIZZAS: " + str(curr_pizzas))
        
        return output
    
    # checks if there are more pizzas in the same request to add all of them to the order
    def checkForMorePizzas(self, tracker):
        pizzas_to_add = []

        group = 1
        new_pizzas_value = next(tracker.get_latest_entity_values('new_pizzas', entity_group=str(group)), None)

        # if i recognize a group with a quantity, then i keep adding the number of pizzas of that group
        while (new_pizzas_value is not None):
            quantity = next(tracker.get_latest_entity_values('quantity', entity_group=str(group)), None)
            quantity = 1 if quantity == None else int(quantity)

            debug(f"Ordering {quantity} {new_pizzas_value}")
            pizzas_to_add.extend([new_pizzas_value for i in range(quantity) ])

            group += 1
            new_pizzas_value = next(tracker.get_latest_entity_values('new_pizzas', entity_group=str(group)), None)

        return pizzas_to_add




class actionAskSomethingMore(Action):
    def name(self) -> Text:
        return "action_ask_something_more"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        pizzas = tracker.get_slot('pizzas') 

        msg = get_order_pizzas_string(pizzas)
        dispatcher.utter_message(response='utter_ask_something_more_order_info', pizzas=msg)

        debug("Pizzas: " + str(pizzas))
        debug("MSG: " + msg)
    
        return []


class ActionSetAddress(Action):
    def name(self) -> Text:
        return "action_set_address"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # simply setting the address here
        # in a real case scenario, further checks on the inserted address may be done with some libraries such as https://github.com/datamade/usaddress
        return [SlotSet("address", tracker.latest_message['text']), SlotSet('current_step', 'utter_ask_time')]


class ActionSetCurrentStepAddress(Action):
    def name(self) -> Text:
        return "action_set_current_step_address"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet('current_step', 'utter_ask_address')]

class ActionSetCurrentStepTelephone(Action):
    def name(self) -> Text:
        return "action_set_current_step_telephone"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet('current_step', 'utter_ask_telephone')]         




class ActionSummary(Action):
    def name(self) -> Text:
        return "action_summary"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        pizzas = tracker.get_slot('pizzas') 
        msg = get_order_pizzas_string(pizzas)
        address = tracker.get_slot('address')
        time = tracker.get_slot('time')
        telephone = tracker.get_slot('telephone')
        store = tracker.get_slot('store')

        dispatcher.utter_message(response="utter_summary", pizzas=msg, address=address, time=time, telephone=telephone, store=store)

        return [SlotSet('current_step', 'action_summary')]


def generate_order_id():
    return secrets.token_urlsafe(12)


class ActionPlaceOrder(Action):
    def name(self) -> Text:
        return "action_place_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # save the current order in case the user need changes/updates
        # in a real case scenario I should save it (i.e. in a db) to then be able to update the status
        # and to keep track of the history of the user
        curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []

        pizzas = tracker.get_slot('pizzas')
        msg = get_order_pizzas_string(pizzas)
        address = tracker.get_slot('address')
        time = tracker.get_slot('time')
        telephone = tracker.get_slot('telephone')
        store = tracker.get_slot('store')

        new_order = {
            "id" : generate_order_id(),
            "pizzas" : pizzas,
            "msg" : msg,
            "address" : address,
            "time" : time,
            "telephone" : telephone,
            "store" : store
        }

        curr_orders.append(new_order)

        dispatcher.utter_message(response="utter_place_order")

        # set the new order and clean the slots
        return [
            SlotSet('store', None), 
            SlotSet('new_pizzas', None), 
            SlotSet('pizzas', None), 
            SlotSet('quantity', None), 
            SlotSet('address', None), 
            SlotSet('time', None), 
            SlotSet('telephone', None), 
            SlotSet('current_step', None), 
            SlotSet('orders', curr_orders), 
            FollowupAction('action_listen')]


# mock function to retrieve the status of the order
def get_order_status(order):
    return random.choice(['in the queue', 'being prepared', 'in the oven', 'getting ready for delivering', 'on the road', 'delivered'])

class ActionGetUpdates(Action):
    def name(self) -> Text:
        return "action_get_updates"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
        debug(curr_orders)

        if len(curr_orders) == 0:
            dispatcher.utter_message(response="utter_get_updates_no_orders")
        elif len(curr_orders) == 1:
            order = curr_orders[0]
            msg = get_order_pizzas_string(order["pizzas"])
            dispatcher.utter_message(response="utter_get_updates", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
        else:
            dispatcher.utter_message(response="utter_get_updates_multiple_orders", n_orders=len(curr_orders))
            for order in curr_orders:
                msg = get_order_pizzas_string(order["pizzas"])
                dispatcher.utter_message(response="utter_get_updates", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )


        return []









class ActionAskChangeOrder(Action):
    def name(self) -> Text:
        return "action_ask_change_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        

        output = []

        # I can change an order being made or already made
        if tracker.get_slot('current_step') is not None:
            dispatcher.utter_message(response='utter_ask_change_order_followup')
        else:
            curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
            debug(curr_orders)
            if len(curr_orders) == 0:
                dispatcher.utter_message(response="utter_ask_cancel_order_no_orders")
            elif len(curr_orders) == 1:
                order = curr_orders[0]
                msg = get_order_pizzas_string(order["pizzas"])
                dispatcher.utter_message(response="utter_ask_change_order", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
                output = [SlotSet('order_id', order['id'])]
            else:
                order_id = tracker.get_slot('order_id')
                # to keep track of which order I need to ask to change
                change_this_order = False
                # if it the first time asking then there should be no order_id set
                # so I inform the user about multiple orders
                if not order_id:
                    dispatcher.utter_message(response="utter_ask_cancel_order_multiple_orders", n_orders=len(curr_orders))
                    change_this_order = True
                for order in curr_orders:
                    # when looping through the orders I will ask for each one of them if it is the one to change
                    # but i need to do one per time and see if the user "intent" is affirm
                    if change_this_order:
                        msg = get_order_pizzas_string(order["pizzas"])
                        dispatcher.utter_message(response="utter_ask_change_order", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
                        change_this_order = False
                        output = [SlotSet('order_id', order['id'])]
                    # if it is not the case then i have to show info for the other one, thus i keep track of the order_id and show the next one of the one which the user "intent" deny
                    else:
                        # so if the previous one was "deny" (order_id set before) then now i set the next to be shown 
                        if order_id == order['id']:
                            change_this_order = True

                # if even the last one is not to be change then I interrupt
                if change_this_order:
                    dispatcher.utter_message(response="utter_change_order_not_doing")
                    dispatcher.utter_message(response="utter_engage")
                    # clean the order_id so next time restart from the first one
                    output = [SlotSet('order_id', None), FollowupAction('action_listen')]



        return output


class ActionChangeOrder(Action):
    def name(self) -> Text:
        return "action_change_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:



        # I can change an order being made or already made
        if tracker.get_slot('current_step') is not None:
            output = [FollowupAction('action_summary')]
            user_intent = tracker.latest_message['intent'].get('name')

            if user_intent != 'choose_pizza' or user_intent != "set_address" or user_intent != "set_time" or user_intent != "set_telephone":
                output = [FollowupAction('action_defaul_fallback')]
            elif user_intent == 'choose_pizza':
                output = [FollowupAction('action_fix_pizzas_choice'), FollowupAction('action_summary')]
            elif user_intent == 'set_address':
                output = [FollowupAction('action_set_address'), FollowupAction('action_summary')]
            
            return output
        else:
            is_affirm = tracker.latest_message['intent'].get('name') == 'affirm'
            if is_affirm:
                # to modify a submitted order you must call the shop
                curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
                order_id = tracker.get_slot('order_id')
                order_to_change = []
                for order in curr_orders:
                    if order['id'] == order_id:
                        order_to_change = order

                dispatcher.utter_message(response='utter_change_order_done', store=order_to_change['store'], store_number=PizzaStoreHelper().get_store_number(order_to_change['store']))

                return []
            else:
                # if the user dont' want to change the order it may be not the one to change
                curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
                # but if there is only one order then I should stop asking
                if len(curr_orders) == 1:
                    dispatcher.utter_message(response="utter_change_order_not_doing")
                    return [FollowupAction('action_listen')]
                else:
                    return [FollowupAction('action_ask_change_order')]














class ActionAskCancelOrder(Action):
    def name(self) -> Text:
        return "action_ask_cancel_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        

        output = []

        # I can cancel an order being made or already made
        if tracker.get_slot('current_step') is not None:
            dispatcher.utter_message(response='utter_ask_cancel_current_order')
        else:
            curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
            debug(curr_orders)
            if len(curr_orders) == 0:
                dispatcher.utter_message(response="utter_ask_cancel_order_no_orders")
            elif len(curr_orders) == 1:
                order = curr_orders[0]
                msg = get_order_pizzas_string(order["pizzas"])
                dispatcher.utter_message(response="utter_ask_cancel_order", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
                output = [SlotSet('order_id', order['id'])]
            else:
                order_id = tracker.get_slot('order_id')
                # to keep track of which order I need to ask to cancel
                cancel_this_order = False
                # if it the first time asking then there should be no order_id set
                # so I inform the user about multiple orders
                if not order_id:
                    dispatcher.utter_message(response="utter_ask_cancel_order_multiple_orders", n_orders=len(curr_orders))
                    cancel_this_order = True
                for order in curr_orders:
                    # when looping through the orders I will ask for each one of them if it is the one to cancel
                    # but i need to do one per time and see if the user "intent" is affirm
                    if cancel_this_order:
                        msg = get_order_pizzas_string(order["pizzas"])
                        dispatcher.utter_message(response="utter_ask_cancel_order", pizzas=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
                        cancel_this_order = False
                        output = [SlotSet('order_id', order['id'])]
                    # if it is not the case then i have to show info for the other one, thus i keep track of the order_id and show the next one of the one which the user "intent" deny
                    else:
                        # so if the previous one was "deny" (order_id set before) then now i set the next to be shown 
                        if order_id == order['id']:
                            cancel_this_order = True

                # if even the last one is not to be cancel then I interrupt
                if cancel_this_order:
                    dispatcher.utter_message(response="utter_cancel_order_not_doing")
                    dispatcher.utter_message(response="utter_engage")
                    # clean the order_id so next time restart from the first one
                    output = [SlotSet('order_id', None), FollowupAction('action_listen')]



        return output


class ActionCancelOrder(Action):
    def name(self) -> Text:
        return "action_cancel_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        is_affirm = tracker.latest_message['intent'].get('name') == 'affirm'


        # I can cancel an order being made or already made
        if tracker.get_slot('current_step') is not None:
            if is_affirm:
                dispatcher.utter_message(response="utter_cancel_order_done")
                dispatcher.utter_message(response="utter_engage")
                return [
                    SlotSet('store', None), 
                    SlotSet('new_pizzas', None), 
                    SlotSet('pizzas', None), 
                    SlotSet('quantity', None), 
                    SlotSet('address', None), 
                    SlotSet('time', None), 
                    SlotSet('telephone', None), 
                    SlotSet('current_step', None), 
                    FollowupAction('action_listen')]
            else:
                return [FollowupAction('action_summary')]
        else:
            if is_affirm:
                curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
                order_id = tracker.get_slot('order_id')

                # mock check if the order cannot be canceled due to status
                order_to_cancel = []
                for order in curr_orders:
                    if order['id'] == order_id:
                        order_to_cancel = order

                if_in_can_cancel_order = ['in the queue', 'being prepared', 'in the oven']
                order_status = get_order_status(order_to_cancel)
                if order_status in if_in_can_cancel_order:
                    new_orders = [order for order in curr_orders if order['id'] != order_id]
                    dispatcher.utter_message(response="utter_cancel_order_done")
                    return [SlotSet('orders', new_orders)]
                else:
                    dispatcher.utter_message(response="utter_cancel_order_not_doable", status=order_status, store=order_to_cancel['store'], store_number=PizzaStoreHelper().get_store_number(order_to_cancel['store']))
                    dispatcher.utter_message(response="utter_engage")
                    return [FollowupAction('action_listen')]
            else:
                # if the user dont' want to cancel the order it may be not the one to cancel
                curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
                # but if there is only one order then I should stop asking
                if len(curr_orders) == 1:
                    dispatcher.utter_message(response="utter_cancel_order_not_doing")
                    return [FollowupAction('action_listen')]
                else:
                    return [FollowupAction('action_ask_cancel_order')]

