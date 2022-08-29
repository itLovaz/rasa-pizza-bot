# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from .utils import PizzaStoreHelper, debug, get_order_items_string, generate_order_id, get_order_status
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, UserUtteranceReverted


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return 'action_default_fallback'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        output = [UserUtteranceReverted()]

        return output

# in case the user set some other slot during the process them i will not ask everything again 
# but go back to the current_step
def get_error_recovery_followup_action(tracker, dispatcher):
    current_step = tracker.get_slot('current_step')
    items = tracker.get_slot('items') 
    address = tracker.get_slot('address')
    time = tracker.get_slot('time')
    telephone = tracker.get_slot('telephone')
    store = tracker.get_slot('store')

    followup_action = None

    if current_step is not None:
        if telephone and time and address and items and store:
            followup_action = 'action_summary'
        elif time and address and items and store:
            followup_action = 'action_set_current_step_telephone'
        elif address and items and store:
            dispatcher.utter_message(response='utter_ask_time')
            followup_action = 'action_listen'
        elif items and store:
            followup_action = 'action_set_current_step_address'
        elif store:
            followup_action = 'action_show_menu'
        else:
            dispatcher.utter_message(response="utter_engage")


    return followup_action


class ActionFunctionNotImplemented(Action):
    def name(self) -> Text:
        return 'action_function_not_implemented'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_step = tracker.get_slot('current_step')
        dispatcher.utter_message(response='utter_function_not_implemented')

        if current_step is not None and (current_step == 'utter_ask_address' or current_step == 'utter_ask_time' or current_step == 'utter_ask_telephone'):
            dispatcher.utter_message(response=current_step)

        return []

class ActionExplain(Action):
    def name(self) -> Text:
        return 'action_explain'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_step = tracker.get_slot('current_step')
        response = 'utter_out_of_scope'

        if current_step is not None and (current_step == 'utter_ask_address' or current_step == 'utter_ask_time' or current_step == 'utter_ask_telephone'):
            dispatcher.utter_message(response=f'{current_step}_explain')
            dispatcher.utter_message(response=current_step)
        else:
            dispatcher.utter_message(response=response)

        return []


class ActionChooseStore(Action):
    # texts = None
    psh = None
    def __init__(self):
        # self.texts = Texts()
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_choose_store"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response='utter_choose_store_searching')
        stores = self.psh.search()
        if len(stores) == 0:
            dispatcher.utter_message(response='utter_choose_store_found_none')
        elif len(stores) == 1:
            dispatcher.utter_message(response='utter_choose_store_found_one', store=next(iter(stores.values())))
        else:
            dispatcher.utter_message(response='utter_choose_store_found')
            for name in stores:
                dispatcher.utter_message(response='utter_single_element', element=name)
            dispatcher.utter_message(response='utter_ask_store')

        # if I change store clean up any left item
        return [SlotSet("items", []), SlotSet('current_step', 'action_choose_store')]

class ActionShowMenu(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_show_menu"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        if store is not None: 
            menu = self.psh.get_pizzas(store)

            dispatcher.utter_message(response='utter_show_menu_results', store=store)
            for pizza in menu:
                dispatcher.utter_message(response='utter_single_element', element=pizza)

            curr_items = tracker.get_slot('items') if tracker.get_slot('items') is not None else []
            if curr_items:
                dispatcher.utter_message(response='utter_current_items', items=get_order_items_string(curr_items))
            else:
                dispatcher.utter_message(response='utter_ask_new_pizzas', store=store)

            return []
        else:
            return [FollowupAction('action_choose_store')]



# adding the choosen items to the list
class actionFixItemsChoice(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_fix_items_choice"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        output = []
        store = tracker.get_slot('store')
        # the user may directly want to order pizzas skipping the store choice
        if store:
            new_items = tracker.get_slot('new_items') 
            curr_items = tracker.get_slot('items') if tracker.get_slot('items') is not None else []


            items_to_add = self.checkForMoreItems(tracker)
            debug("NEW ITEMS: " + str(new_items))
            debug("CURR ITEMS: " + str(curr_items))
            debug("TO ADD ITEMS: " + str(items_to_add))

            # in case I order multiple items I add them all, otherwise only the one given
            # but i check that the pizzas are available for that store
            availables, not_availables = self.psh.filter_pizza_choice(store, items_to_add if items_to_add else new_items)
            curr_items.extend(availables)
            if not_availables:
                dispatcher.utter_message(text=f"The following pizzas are not available at {store}: {', '.join(not_availables)}")
            
            # if no items were added then I should show the menu again
            output = [SlotSet("items", curr_items), SlotSet('current_step', 'action_ask_something_more')]
            if len(curr_items) == 0:
                output = [FollowupAction('action_show_menu')]

            debug("CURR ITEMS: " + str(curr_items))
        else:
            dispatcher.utter_message(text='Sorry, first I need to know from which store you want to order')
            output = [FollowupAction('action_choose_store')]
        
        return output
    
    # checks if there are more items in the same request to add all of them to the order
    def checkForMoreItems(self, tracker):
        items_to_add = []

        group = 1
        new_items_value = next(tracker.get_latest_entity_values('new_items', entity_group=str(group)), None)

        # if i recognize a group with a quantity, then i keep adding the number of items of that group
        while (new_items_value is not None):
            quantity = next(tracker.get_latest_entity_values('quantity', entity_group=str(group)), None)
            quantity = 1 if quantity == None else int(quantity)

            debug(f"Ordering {quantity} {new_items_value}")
            items_to_add.extend([new_items_value for i in range(quantity) ])

            group += 1
            new_items_value = next(tracker.get_latest_entity_values('new_items', entity_group=str(group)), None)

        return items_to_add




class actionAskSomethingMore(Action):
    def name(self) -> Text:
        return "action_ask_something_more"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        items = tracker.get_slot('items') 

        msg = get_order_items_string(items)
        dispatcher.utter_message(response='utter_ask_something_more_order_info', items=msg)
    
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
        # if the user changed a value but already did other steps of the process then i go back to the current step
        error_recovery_followup_action = get_error_recovery_followup_action(tracker, dispatcher)
        if error_recovery_followup_action is not None and error_recovery_followup_action != 'action_set_current_step_address':
            return [FollowupAction(error_recovery_followup_action)]
        else:
            return [SlotSet('current_step', 'utter_ask_address')]

class ActionSetCurrentStepTelephone(Action):
    def name(self) -> Text:
        return "action_set_current_step_telephone"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # if the user changed a value but already did other steps of the process then i go back to the current step
        error_recovery_followup_action = get_error_recovery_followup_action(tracker, dispatcher)
        if error_recovery_followup_action is not None and error_recovery_followup_action != 'action_set_current_step_telephone':
            return [FollowupAction(error_recovery_followup_action)]
        else:
            return [SlotSet('current_step', 'utter_ask_telephone')]         


class ActionSummary(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_summary"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # in case the user set's more slot in one phrase then I check to have everything before sending the order
        output = []

        items = tracker.get_slot('items') 
        address = tracker.get_slot('address')
        time = tracker.get_slot('time')
        telephone = tracker.get_slot('telephone')
        store = tracker.get_slot('store')


        if items and address and time and telephone and store:
            msg = get_order_items_string(items)
            total = self.psh.get_total_price(store, items)
            dispatcher.utter_message(response="utter_summary", items=msg, address=address, time=time, telephone=telephone, store=store, total=total)

            output = [SlotSet('current_step', 'action_summary')]
        # go back to the required slot filling action
        else:
            dispatcher.utter_message(response='utter_missing_something')
            if not store:
                output = [SlotSet('current_step', 'action_choose_store'), FollowupAction('action_choose_store')]
            elif not items:
                output = [SlotSet('current_step', 'action_ask_something_more'), FollowupAction('action_show_menu')]
            elif not address:
                output = [SlotSet('current_step', 'utter_ask_address'), FollowupAction('action_set_current_step_address')]
            elif not time:
                dispatcher.utter_message(response='utter_ask_time')
                output = [SlotSet('current_step', 'utter_ask_time'), FollowupAction('action_listen')]
            elif not telephone:
                output = [SlotSet('current_step', 'utter_ask_telephone'), FollowupAction('action_set_current_step_telephone')]

        return output



class ActionPlaceOrder(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_place_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # save the current order in case the user need changes/updates
        # in a real case scenario I should save it (i.e. in a db) to then be able to update the status
        # and to keep track of the history of the user
        curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []

        store = tracker.get_slot('store')
        items = tracker.get_slot('items')
        msg = get_order_items_string(items)
        total = self.psh.get_total_price(store, items)
        address = tracker.get_slot('address')
        time = tracker.get_slot('time')
        telephone = tracker.get_slot('telephone')

        new_order = {
            "id" : generate_order_id(),
            "items" : items,
            "msg" : msg,
            "total" : total,
            "address" : address,
            "time" : time,
            "telephone" : telephone,
            "store" : store
        }

        curr_orders.append(new_order)

        dispatcher.utter_message(response="utter_place_order")

        # set the new order and clean the slots
        return [
            SlotSet('item', None), 
            SlotSet('typology', None), 
            SlotSet('pizza', None), 
            SlotSet('store', None), 
            SlotSet('new_items', None), 
            SlotSet('items', None), 
            SlotSet('quantity', None), 
            SlotSet('address', None), 
            SlotSet('time', None), 
            SlotSet('telephone', None), 
            SlotSet('current_step', None), 
            SlotSet('orders', curr_orders), 
            FollowupAction('action_listen')]



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
            msg = get_order_items_string(order["items"])
            dispatcher.utter_message(response="utter_get_updates", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
        else:
            dispatcher.utter_message(response="utter_get_updates_multiple_orders", n_orders=len(curr_orders))
            for order in curr_orders:
                msg = get_order_items_string(order["items"])
                dispatcher.utter_message(response="utter_get_updates", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )


        return []


class ActionAskChangeOrder(Action):
    def name(self) -> Text:
        return "action_ask_change_order"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        

        output = []

        # I can change an order being made or already made
        if tracker.get_slot('current_step') is not None and tracker.get_slot("items") is not None:
            print('here')
            dispatcher.utter_message(response='utter_ask_change_order_followup')
        else:
            curr_orders = tracker.get_slot('orders') if tracker.get_slot('orders') is not None else []
            debug(curr_orders)
            if len(curr_orders) == 0:
                dispatcher.utter_message(response="utter_ask_cancel_order_no_orders")
            elif len(curr_orders) == 1:
                order = curr_orders[0]
                msg = get_order_items_string(order["items"])
                dispatcher.utter_message(response="utter_ask_change_order", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
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
                        msg = get_order_items_string(order["items"])
                        dispatcher.utter_message(response="utter_ask_change_order", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
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
                output = [FollowupAction('action_fix_items_choice'), FollowupAction('action_summary')]
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

                dispatcher.utter_message(response='utter_change_order_done', store=order_to_change['store'], store_number=PizzaStoreHelper().get_telephone(order_to_change['store']))

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
                msg = get_order_items_string(order["items"])
                dispatcher.utter_message(response="utter_ask_cancel_order", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
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
                        msg = get_order_items_string(order["items"])
                        dispatcher.utter_message(response="utter_ask_cancel_order", items=msg, address=order["address"], time=order["time"], telephone=order["telephone"], store=order["store"], status=get_order_status(order) )
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
                    SlotSet('item', None), 
                    SlotSet('typology', None), 
                    SlotSet('pizza', None), 
                    SlotSet('store', None), 
                    SlotSet('new_items', None), 
                    SlotSet('items', None), 
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
                    dispatcher.utter_message(response="utter_cancel_order_not_doable", status=order_status, store=order_to_cancel['store'], store_number=PizzaStoreHelper().get_telephone(order_to_cancel['store']))
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




class actionShowDrinks(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_show_drinks"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        if store is not None: 
            menu = self.psh.get_drinks(store)

            dispatcher.utter_message(response='utter_show_drink', store=store)
            for drink in menu:
                dispatcher.utter_message(response='utter_single_element', element=drink)

            curr_items = tracker.get_slot('items') if tracker.get_slot('items') is not None else []
            if curr_items:
                dispatcher.utter_message(response='utter_current_items', items=get_order_items_string(curr_items))

            return []
        else:
            return [FollowupAction('action_choose_store')]


class actionShowIngredients(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_show_ingredients"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        pizza = tracker.get_slot('pizza')
        if store is not None: 
            if pizza is not None:
                ingredients = self.psh.get_pizza_ingredients(store, pizza)
                if ingredients is not None:
                    dispatcher.utter_message(response='utter_show_ingredients', ingredients=ingredients, pizza=pizza)
                else:
                    dispatcher.utter_message(response='utter_show_ingredients_no_pizza', pizza=pizza, store=store)
            else:
                dispatcher.utter_message(response='utter_ask_rephrase')
            return []
        else:
            return [FollowupAction('action_choose_store')]

class actionShowPrice(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return 'action_show_price'
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        item = tracker.get_slot('item') if tracker.get_slot('item') is not None else tracker.get_slot('pizza')
        if store is not None: 
            if item is not None:
                price = self.psh.get_item_price(store, item)
                if price is not None:
                    dispatcher.utter_message(response='utter_show_price', price=price, item=item)
                else:
                    dispatcher.utter_message(response='utter_show_price_no_item', item=item, store=store)
            else:
                dispatcher.utter_message(response='utter_ask_rephrase')
            return []
        else:
            return [FollowupAction('action_choose_store')]

class actionShowFilteredMenu(Action):
    psh = None
    def __init__(self):
        self.psh = PizzaStoreHelper()
    def name(self) -> Text:
        return "action_show_filtered_menu"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        store = tracker.get_slot('store')
        typology = tracker.get_slot('typology')
        if store is not None: 
            if typology is not None:
                menu = self.psh.get_filtered_pizzas(store, typology)
                dispatcher.utter_message(response='utter_show_filtered_menu', store=store)
                for pizza in menu:
                    dispatcher.utter_message(response='utter_single_element', element=pizza)
                curr_items = tracker.get_slot('items') if tracker.get_slot('items') is not None else []
                if curr_items:
                    dispatcher.utter_message(response='utter_current_items', items=get_order_items_string(curr_items))
                else:
                    dispatcher.utter_message(response='utter_ask_new_pizzas', store=store)
            else:
                dispatcher.utter_message(response='utter_ask_rephrase')
            return []
        else:
            return [FollowupAction('action_choose_store')]