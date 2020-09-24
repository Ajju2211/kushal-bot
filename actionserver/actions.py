from typing import Any, Text, Dict, List, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import UserUtteranceReverted, UserUttered,  FollowupAction
# from rasa_core.events import (UserUtteranceReverted, UserUttered,
#                               ActionExecuted, Event)
from rasa_sdk.events import AllSlotsReset, SlotSet
import pandas as pd
from rasa.core.slots import Slot
import json
from actionserver.utils import utilities as util
from actionserver.controllers.faqs.faq import FAQ
from actionserver.controllers.regexPatterns import *
import logging
import secrets
import traceback
import re

dish_list = []
quant_list = []  # takes quantity from user
restaurant_dataset = pd.read_csv('./actionserver/restaurant.csv')
restaurant_dataset = restaurant_dataset.set_index(
    'restaurant').T.to_dict('list')

logger = logging.getLogger(__name__)


REQUESTED_SLOT = "requested_slot"


INVALID_VALUE = str(secrets.token_hex(20))

with open(r'.\actionserver\custom_payload.json') as f:
    restaurant_menu = json.load(f)

# Code snippet for global back
# return [Restarted(), UserUttered(text="/get_started", parse_data={
    #   "intent": {"confidence": 1.0, "name": "get_started"},
    #   "entities": []
    #  }), FollowupAction(name="utter_greet")]


def query_back(dispatcher):
    dispatcher.utter_message("Going back to queries!!!")
    greet_utter = UserUttered(text="/greet", parse_data={
        "intent": {"confidence": 1.0, "name": "greet"},
        "entities": []
    })

    query_utter = UserUttered(text="/query_init", parse_data={
        "intent": {"confidence": 1.0, "name": "query_init"},
        "entities": []
    })

    return [
        greet_utter,
        FollowupAction(name="utter_greet"),
        query_utter,
        FollowupAction(name="utter_query_type")
    ]


def greet_back(dispatcher):
    dispatcher.utter_message("Going back!!!")
    return [UserUttered(text="/greet", parse_data={
        "intent": {"confidence": 1.0, "name": "greet"},
        "entities": []
    }), FollowupAction(name="utter_greet")]


class ActionGreetBack(Action):
    def name(self) -> Text:
        return "action_greet_back"

    def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        return greet_back(dispatcher)


class InfoForm(FormAction):

    """Collects order information"""

    def name(self):
        return "info_form"

    @staticmethod
    def required_slots(tracker):
        return [
            "username",
            "mailid",
            "phone_number",
            "confirm"
        ]

    @staticmethod
    def msg() -> List[Text]:
        return ["back1", "back2", "back3"]

    def validate_mailid(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value.lower() not in self.msg():
            return {"mailid": value}
        else:
            return {"mailid": None, "username": None}

    def validate_phone_number(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value.lower() not in self.msg():
            return {"phone_number": value}
        else:
            return {"phone_number": None, "mailid": None}

    def validate_confirm(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value.lower() not in self.msg():
            return {"phone_number": value}
        else:
            return {"phone_number": None, "confirm": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        username = tracker.get_slot("username")
        mailid = tracker.get_slot("mailid")
        phone_number = tracker.get_slot("phone_number")

        message = "DETAILS:"+"\n\n"+"Name:"+username+"\n"+"Email:"+mailid+"\n" + \
            "Phone Number:"+phone_number+"\n"+"\nThanks! for sharing information."
        saveFile = open("some.txt", 'a')
        saveFile.write(message)
        saveFile.close()
        dispatcher.utter_message(message)
        return []


class UserInfoForm(FormAction):

    """Collects order information"""

    def name(self):
        return "user_info_form"

    @staticmethod
    def required_slots(tracker):
        if tracker.get_slot("area"):
            return ["confirm"]
        elif tracker.get_slot("phone_number"):
            return ["area"]
        elif tracker.get_slot("mailid"):
            return ["phone_number"]
        elif tracker.get_slot("username"):
            return ["mailid"]
        else:
            return ["username"]

        return [
            "username",
            "mailid",
            "phone_number",
            "area",
            "confirm"
        ]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {"username": self.from_text(), "mailid": [self.from_entity("email"), self.from_text()],
                "phone_number": [self.from_entity("ind_num"), self.from_text()],
                "area": [self.from_entity("area"), self.from_text()],
                "confirm": [self.from_entity("confirm"), self.from_text()]}

    def validate_username(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value:
            return {"username": value, REQUESTED_SLOT: "mailid"}
        else:
            dispatcher.utter_message(text="something happened,re type..")
            return {"username": None, REQUESTED_SLOT: "username"}

    def validate_mailid(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("email: ",value)
        if value:
            if value.lower() == "back":
                return {"mailid": None, "username": None, REQUESTED_SLOT: "username"}
            else:
                match = re.search(pattern=EMAIL_PATTERN, string=value.strip())
                if match:
                    # entity = {
                    # "start": match.pos,
                    # "end": match.endpos,
                    # "value": match.group(),
                    # "confidence": 1.0,
                    # "entity": d['name'],
                    #     }
                    return {"mailid": match.group(), REQUESTED_SLOT: "phone_number"}
                else:
                    dispatcher.utter_message(
                        text="Can you please enter valid email!")
                    return {"mailid": None, REQUESTED_SLOT: "mailid"}
        else:
            dispatcher.utter_message(text="Can you please enter valid email!")
            return {"mailid": None, REQUESTED_SLOT: "mailid"}

    def validate_phone_number(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value:
            if value.lower() == "back":
                return {"phone_number": None, "mailid": None, REQUESTED_SLOT: "mailid"}
            else:
                match = re.search(pattern=IND_NUM_PATTERN,
                                  string=value.strip())
                if match:
                    return {"phone_number": match.group(), REQUESTED_SLOT: "area"}
                else:
                    dispatcher.utter_message(
                        text="Please enter valid indian numbers only")
                    return {"phone_number": None, REQUESTED_SLOT: "phone_number"}
        else:
            dispatcher.utter_message(
                text="Please enter valid indian numbers only")
            return {"phone_number": None, REQUESTED_SLOT: "phone_number"}

    def validate_area(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print("areas: ",value)
        if value:
            areas = ["thane","csmt","mulund","matunga"]
            if value.lower() == "back":
                return {"area": None, "phone_number": None, REQUESTED_SLOT: "phone_number"}
            elif value.lower in areas:
                return {"area": value, REQUESTED_SLOT: "confirm"}
            elif value.lower() == "exit":
                return {"area": "EXIT", "confirm": INVALID_VALUE,REQUESTED_SLOT:None}
            else:
                exit_button = [
                    {
                    "title":"Exit",
                    "payload":"/inform{\"area\":\"EXIT\"}"
                }]
                dispatcher.utter_message(text="Currently we serve only in areas like Thane|CSMT|Mulund|Matunga of mumbai",buttons=exit_button)
                return {"area": None, REQUESTED_SLOT:"area"}
        else:
            return {"area": None, REQUESTED_SLOT:"area"}

    def validate_confirm(
        self,
        value: Text,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value:
            confirm = ["yes", "confirm", "s", "sure"]
            cancel = ["no", "cancel", "not", "remove", "nope"]
            if value.lower() == "back":
                return {"confirm": None, "phone_number": None, REQUESTED_SLOT: "phone_number"}
            elif value.lower() in confirm:
                return {"confirm": "YES"}
            elif value.lower() in cancel:
                return {"confirm": "NO"}
            else:
                dispatcher.utter_message(
                    text="Please enter valid option")
                return {"confirm": None, REQUESTED_SLOT: "confirm"}
        else:
            dispatcher.utter_message(text="please say yes or no!")
            return {"confirm": None, REQUESTED_SLOT: "confirm"}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        confirm = tracker.get_slot("confirm")
        area = tracker.get_slot("area")
        if area == "EXIT":
            dispatcher.utter_message(
                "Thanks for visiting Kushal's Veggie Mart")
            return []
        if confirm == "YES":
            dispatcher.utter_message(
                "Thanks for Ordering!, your order is on the way")
            return []
        if confirm == "NO":
            dispatcher.utter_message("Your order has been cancelled !!")
            dispatcher.utter_message(
                "Thanks for visiting Kushal's Veggie Mart")
            return []
        # username = tracker.get_slot("username")
        # mailid = tracker.get_slot("mailid")
        # phone_number = tracker.get_slot("phone_number")

        # message = "DETAILS:"+"\n\n"+"Name:"+username+"\n"+"Email:"+mailid+"\n" + \
        #     "Phone Number:"+phone_number+"\n"+"\nThanks! for sharing information."
        # saveFile = open("some.txt", 'a')
        # saveFile.write(message)
        # saveFile.close()


class ActionShowMenu(Action):
    def name(self) -> Text:
        return "action_show_menu"

    def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        x = open('./actionserver/custom_payload.json', "r")
        data = json.load(x)
        data_restaurant = data['restaurant']
        for i in data['restaurant']['menu_imgs']:
            url = str(i)
            dispatcher.utter_message("Menu of the Kushal's Veggie is ")
            dispatcher.utter_message(image=url)
        return []


class ActionAskDishCategory(Action):
    def name(self) -> Text:
        return "action_ask_dish_category"

    def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        data = [
            {"label": "starters1", "value": "/inform{'dish_category':'starters'}"},
            {"label": "meals1", "value": "/inform{'dish_category':'meals'}"}
        ]

        message = {"payload": "dropDown", "data": data}

        dispatcher.utter_message(
            text="Please select a option", json_message=message)
        print("inside dish_category")
        return []


class OrderForm(FormAction):

    def name(self):
        return "order_form"

    @staticmethod
    def required_slots(tracker):
        if tracker.get_slot("quantity"):
            return [
                "proceed"
            ]
        elif tracker.get_slot("dish_name"):
            return [
                "quantity",
                "proceed"
            ]
        elif tracker.get_slot("dish_category"):
            return [
                "dish_name"
            ]
        else:
            return [
                "dish_category"
                # "dish_name",
                # "quantity",
                # "proceed"
            ]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        # return {"dish_category": self.from_intent("inform"),"dish_name": self.from_entity("any_thing"),"quantity": self.from_entity("quantity"),"proceed": self.from_intent("inform")}
        # return {"dish_category": [self.from_intent("inform"),self.from_text()], "dish_name": self.from_text(), "quantity": self.from_entity("quantity"), "proceed": self.from_intent("inform")}
        return {
            "dish_category": [
                self.from_entity("dish_category"),
                self.from_text()
            ],
            "dish_name": [
                self.from_entity("dish_name"),
                self.from_text()
            ],
            "quantity": self.from_entity("quantity"),
            "proceed": self.from_intent("inform")
        }

    def request_next_slot(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ):
        """Request the next slot and utter template if needed,
            else return None"""

        for slot in self.required_slots(tracker):
            if self._should_request_slot(tracker, slot):
                logger.debug(f"Request next slot '{slot}'")
                if slot == "dish_category":
                    # dispatcher.utter_message(text="Please select the category")
                    button_resp = [
                        {
                            "title": "Back",
                            "payload": '/inform{"dish_category":"back"}'
                        }
                    ]
                    # dispatcher.utter_message(
                    #     buttons=button_resp)
                    self.askCategories(dispatcher)
                elif slot == "quantity":
                    button_resp = [
                        {
                            "title": "Back",
                            "payload": '/inform{"quantity":"back"}'
                        }
                    ]
                    dispatcher.utter_message(buttons=button_resp)
                    self.askQuantity(dispatcher, tracker)
                else:
                    dispatcher.utter_message(
                        template=f"utter_ask_{slot}", **tracker.slots)
                return [SlotSet(REQUESTED_SLOT, slot)]

        # no more required slots to fill
        return None

    def askCategories(self, dispatcher):
        data = []
        for keys in restaurant_menu['restaurant']['menu'].keys():
            val = '\"{}\"'.format(keys)
            cat = {"label": f"{keys}",
                   "value": '/inform{\"dish_category\":'+val+'}'}
            data.append(cat)

        message = {"payload": "dropDown", "data": data}
        button_resp = [
            {
                "title": "back",
                "payload": '/inform{"dish_category":"back"}'
            }
        ]
        # dispatcher.utter_message(buttons=button_resp)

        dispatcher.utter_message(
            text="Please select a option", json_message=message, buttons=button_resp)
    # To display dishes of category

    def askQuantity(self, dispatcher, tracker):
        dish_name = tracker.get_slot("dish_name")
        print('dish_name in askQuantity', dish_name)
        dish_category = tracker.get_slot("dish_category")
        data = []
        for item in restaurant_menu['restaurant']['menu'][dish_category]:
            if item['dish'].lower() == dish_name.lower():
                for price in item['price']:
                    label = str(price['cost']) + '₹' + '/' + \
                        str(price['quantity']) + str(price['unit'])
                    value = json.dumps(price)
                    print("strof priceObj ", value)
                    ct = {
                        "label": f"{label}",
                        "value": '/inform{\"quantity\":'+value+'}'
                    }
                    data.append(ct)
                message = {"payload": "dropDown", "data": data}
        dispatcher.utter_message(
            text="Please select a option", json_message=message)

    def showDishes(self, category, dispatcher, tracker):
        dic = {}
        data = []
        print(f"cat-received:{category}")
        try:
            if restaurant_menu['restaurant']['menu'][category]:
                temp = restaurant_menu['restaurant']['menu'][category]
                for j in temp:
                    Price = ""
                    Quant = ""
                    for i in j['price']:
                        Price += str(i['cost']) + '₹' + '/' + \
                            str(i['quantity']) + '' + str(i['unit'])+','
                        Quant += '/' + str(i['unit'])+','
                    dic = {
                        "title": j['dish'],
                        "price": Price,
                        "image": j['image'],
                        "quantity": Quant,
                    }

                    data.append(dic)

            message = {"payload": "cartCarousels", "data": data}

            dispatcher.utter_message(
                text="Please type the dish name", json_message=message)

            # return {"dish_category": category}

        except Exception as e:
            dispatcher.utter_message(text="No such Category Found")
            traceback.print_exc()
            raise Exception("No such Category")
            # return {"dish_category":None}

    def showCart(self, dispatcher, tracker):
        data = []
        for x in dish_list:
            image = util.dish_info(x['dish'], x['category'])['image']
            # price = util.dish_info(x['dish'], x['category'])['price']
            price = str(x['cost'])+"₹"

            qty = str(x['quantity']['quantity'])+str(x['quantity']['unit'])
            cart = {
                "title": x['dish'],
                "image": image,
                "quantity": qty,
                "price": price
            }

            data.append(cart)

        message = {"payload": "cartCarousels", "data": data}

        dispatcher.utter_message(text="Your Order", json_message=message)

    def validate_dish_category(self,
                               value: Text,
                               dispatcher: CollectingDispatcher,
                               tracker: Tracker,
                               domain: Dict[Text, Any],
                               ) -> Dict[Text, Any]:

        data = []
        category = value
        if value:
            if value.lower() == 'back':
                return {
                    "dish_category": INVALID_VALUE,
                    "dish_name": INVALID_VALUE,
                    "quantity": INVALID_VALUE,
                    "proceed": INVALID_VALUE
                }
            else:
                try:
                    button_resp = [
                        {
                            "title": "back",
                            "payload": '/inform{"dish_name":"back1"}'
                        }
                    ]

                    # dispatcher.utter_message(text="type back otherwise!", buttons=button_resp)

                    self.showDishes(category, dispatcher, tracker)
                    return {"dish_category": category}
                except Exception as e:
                    print(e)
                    return {"dish_category": None}
        else:
            return [SlotSet("dish_category", None), SlotSet(REQUESTED_SLOT, "dish_category")]

        # message={"payload":"cartCarousels","data":data}

        # dispatcher.utter_message(text="Please type the dish name",json_message=message)

        # return {"dish_category": category}

    def validate_dish_name(self,
                           value: Text,
                           dispatcher: CollectingDispatcher,
                           tracker: Tracker,
                           domain: Dict[Text, Any],
                           ) -> Dict[Text, Any]:
        if value:
            value = value.lower()
            if value == "back" or value == "back1":
                return {
                    "dish_category": None,
                    "dish_name": None,
                    "quantity": None,
                    "proceed": None,
                    REQUESTED_SLOT: "dish_category"
                }
            else:

                category = tracker.get_slot("dish_category")

                # to debug whether the slot is present
                print(category)

                dish_name = value
                menu = restaurant_menu['restaurant']['menu']
                if menu[category]:
                    temp = menu[category]
                    for j in temp:
                        if dish_name.lower() == j['dish'].lower():
                            price = ""
                            for p in j['price']:
                                price += f'{p["cost"]} ₹ per {p["quantity"]} {p["unit"]} \n'
                            dispatcher.utter_message(text=price)
                            return {"dish_name": dish_name}
                        else:
                            continue
                            # dispatcher.utter_template("utter_not_serving",tracker)
                            # return {"dish_name":None}
                    dispatcher.utter_template("utter_not_serving", tracker)
                    return {"dish_name": None}
                else:
                    dispatcher.utter_message(text="No such category found")

        # if dish_name in dataset.keys():
        #     dispatcher.utter_message("it costs {}".format(dataset[dish_name][0]))
        #     return {"dish_name": dish_name}
        # else:
        #     dispatcher.utter_template("utter_not_serving",tracker)
        #     return {"dish_name":None}

    def validate_quantity(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        dish_name = tracker.get_slot("dish_name")

        try:
            quantity = tracker.get_slot("quantity")
            return {"dish_name": dish_name, "quantity": quantity}
        except:
            dispatcher.utter_message(text="Please Select above options")
            return {"dish_name": dish_name, "quantity": None}

    def validate_proceed(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        dish_name = tracker.get_slot("dish_name")
        proceed = tracker.get_slot("proceed")
        # quant = json.loads(tracker.get_slot("quantity"))
        quant = tracker.get_slot("quantity")
        cat = tracker.get_slot("dish_category")
        if proceed == "Add to Cart":
            dish_obj = {"dish": dish_name, "quantity": quant,
                        "cost": quant['cost'], "category": cat}
            dish_list.append(dish_obj)
            self.showDishes(cat, dispatcher, tracker)
            print("quantity")
            return {"proceed": None, "dish_name": None, "quantity": None}

        elif proceed == "Buy Now":
            dish_obj = {"dish": dish_name, "quantity": quant,
                        "cost": quant['cost'], "category": cat}
            dish_list.append(dish_obj)
            return {"proceed": proceed}

        else:
            # Select other food
            self.showDishes(cat, dispatcher, tracker)
            return {"dish_name": None, "proceed": None, "quantity": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        if tracker.get_slot("dish_category") == INVALID_VALUE:
            li = [
                SlotSet("dish_category", None),
                SlotSet("dish_name", None),
                SlotSet("quantity", None),
                SlotSet("proceed", None)
            ]
            li.extend(greet_back(dispatcher))
            return li

        else:

            amount = 0
            dish_cat = tracker.get_slot("dish_category")
            total = 0
            price = 0

            for x in dish_list:
                # prize = util.dish_info(x['dish'], x['category'])['price']
                prize = x['cost']
                total = float(prize)
                amount += total
                # dispatcher.utter_message("{} : {} : {}".format(x['dish'],x["quantity"],total))
                # amount += total

            dispatcher.utter_message("Total Amount : {}".format(amount))
            self.showCart(dispatcher, tracker)
            dispatcher.utter_message("Total Amount : {}".format(amount))
            dispatcher.utter_message("Thanks for ordering")
            return [AllSlotsReset()]


class DefaultFallback(FormAction):
    """Default Fallback Action"""

    def name(self):
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        queryText = tracker.latest_message.get('text')

        dispatcher.utter_message(
            "Fallback Triggered bcoz u've typed something! "+queryText)
        return []


class ComplainForm(FormAction):

    def name(self):
        return "complain_form"

    @staticmethod
    def required_slots(tracker):

        if tracker.get_slot("complain_type"):
            return ["complain_type", "complain_text"]
        else:
            return ["complain_type"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {"complain_type": [self.from_entity("complain_type"), self.from_text()], "complain_text": [self.from_entity(entity="navigation"), self.from_text()]}

        # return {"complain_type": self.from_entity("complain_type"),"complain_text": self.from_entity(entity="any_thing")}

    def validate_complain_type(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        complaints = ["quality", "mis behaviour", "kushal app", "other"]
        value = value.strip().lower()
        if value == "back1" or value == "back":
            return {"complain_type": INVALID_VALUE, "complain_text": INVALID_VALUE}
        elif value in complaints:
            return {"complain_type": value}
        else:
            dispatcher.utter_message("please type valid option.")
            return {"complain_type": None}

    def validate_complain_text(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        if value == "back2" or value.lower() == "back":
            return {"complain_type": None, "complain_text": None}
        else:
            return {"complain_text": value}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        if tracker.get_slot("complain_type") != INVALID_VALUE:
            # saving
            with open("./actionserver/customer_queries.json", "r") as queriesRef:
                comp_type = tracker.get_slot("complain_type")
                comp = tracker.get_slot("complain_text")
                compObj = json.load(queriesRef)
                compObj["complaints"].append({
                    "createdOn": util.timestamp(),
                    "complaint_area": comp_type,
                    "complaint": comp
                })
                with open("./actionserver/customer_queries.json", "w") as queriesRefWrite:
                    json.dump(compObj, queriesRefWrite, indent=4)

            dispatcher.utter_message("Your Complaint :\n Complaint Area:{comp_type}\n Complaint: '{comp}' \n has been registered!".format(
                comp_type=comp_type, comp=comp))
        else:
            dispatcher.utter_message("Complaints Form is closed")
            li = [SlotSet("complain_type", None),
                  SlotSet("complain_text", None)]
            li.extend(query_back(dispatcher))
            return li
        return [SlotSet("complain_type", None), SlotSet("complain_text", None)]


class FeedbackForm(FormAction):

    def name(self):
        return "feedback_form"

    @staticmethod
    def required_slots(tracker):
        if tracker.get_slot("rating"):
            return ["rating", "feedback_text"]
        else:
            return ["rating"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""
        # return {"rating": [self.from_entity("rating"),self.from_entity("any_thing")],"feedback_text": [self.from_entity(entity="any_thing"),self.from_entity(entity="navigation")]}
        return {"rating": [self.from_entity("rating"), self.from_text()], "feedback_text": [self.from_text(), self.from_entity(entity="navigation")]}

    def validate_rating(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        ratings = ['1', '2', '3', '4', '5']
        try:
            value = value.strip()
            if value == "back1" or value.lower() == "back":
                return {"rating": INVALID_VALUE, "feedback_text": INVALID_VALUE}
                # 1-5 it integer otherwise rating:None
            elif value in ratings:
                return {"rating": value, "feedback_text": None}
            else:
                dispatcher.utter_message("Please enter valid option.")
                return {"rating": None, "feedback_text": None}
        except Exception as e:
            print(e)
            dispatcher.utter_message("Please enter valid option.")
            return {"rating": None, "feedback_text": None}

    def validate_feedback_text(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if value == "back2" or value.lower() == "back":
            return {"rating": None, "feedback_text": None}
        else:
            return {"feedback_text": value}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        if tracker.get_slot("rating") != INVALID_VALUE:
            with open("./actionserver/customer_queries.json", "r") as queriesRef:
                rating = tracker.get_slot("rating")
                feedback = tracker.get_slot("feedback_text")
                feedbackObj = json.load(queriesRef)
                feedbackObj["feedback"].append({
                    "createdOn": util.timestamp(),
                    "complaint_area": rating,
                    "complaint": feedback
                })
            with open("./actionserver/customer_queries.json", "w") as queriesRefWrite:
                json.dump(feedbackObj, queriesRefWrite, indent=4)

            dispatcher.utter_message("Your Response :\n Rating :'{rate}' star \n Feedback: '{feedbk}' \n Submitted!Thank You!".format(
                rate=rating, feedbk=feedback))
        else:
            dispatcher.utter_message("Feedback form closed")
            li = [SlotSet("rating", None), SlotSet("feedback_text", None)]
            li.extend(query_back(dispatcher))
            return li
        return [SlotSet("rating", None), SlotSet("feedback_text", None)]


class FaqForm(FormAction):

    def name(self):
        return "faq_form"

    @staticmethod
    def required_slots(tracker):
        if tracker.get_slot("faq_choice"):
            if tracker.get_slot("faq_choice") == '2':
                return ["faq_text"]
            else:
                return ['faq_choice']
        else:
            return ['faq_choice']
        # return ["faq_choice","faq_text"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        # return { "faq_choice": self.from_entity("faq_choice"),"faq_question": self.from_entity("faq_question"), "faq_text": [self.from_text()]}

        return {"faq_choice": [self.from_entity("faq_choice"), self.from_text()], "faq_text": [self.from_text(), self.from_entity(entity="navigation")]}

    def validate_faq_choice(self,
                            value: Text,
                            dispatcher: CollectingDispatcher,
                            tracker: Tracker,
                            domain: Dict[Text, Any],
                            ) -> Dict[Text, Any]:
        # faq_choice = tracker.get_slot("faq_choice")
        faq_choice = value
        print(f"Inside validate faq choice {faq_choice}")

        if faq_choice == "back2" or value.lower() == 'back':
            # return {"faq_choice": INVALID_VALUE,"faq_text":INVALID_VALUE}
            return {"faq_choice": INVALID_VALUE, "faq_text": INVALID_VALUE}

        elif faq_choice == "1":
            useNlp = False
            faq_data = pd.read_csv(
                "./actionserver/controllers/faqs/test_faq.csv")

            button_resp = [
                {
                    "title": "Choose from our set of FAQs",
                    "payload": "/faq_choice{\"faq_choice\": \"1\"}"
                },
                {
                    "payload": "/faq_choice{\"faq_choice\": \"2\" }",
                    "title": "Type your own question."
                }, {
                    "payload": "/faq_choice{\"faq_choice\": \"back2\"}",
                    "title": "Back"
                }
            ]
            dispatcher.utter_message(
                text="How should we get your FAQ?", buttons=button_resp)
            qa = []
            for i in range(len(faq_data)):
                obj = {
                    "title": faq_data["Question"][i],
                    "description": faq_data["Answer"][i]
                }
                qa.append(obj)
            message = {"payload": "collapsible", "data": qa}
            dispatcher.utter_message(text="Faq's", json_message=message)

            return {
                "faq_choice": None,
                REQUESTED_SLOT: "faq_choice"
            }

        elif faq_choice == '2':
            return {
                "faq_choice": value,
                REQUESTED_SLOT: "faq_text"
            }

        else:
            dispatcher.utter_message(text="Please type valid option")
            return {
                "faq_choice": None,
                REQUESTED_SLOT: "faq_choice"
            }

    def validate_faq_text(self,
                          value: Text,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: Dict[Text, Any],
                          ) -> Dict[Text, Any]:
        faq_choice = tracker.get_slot("faq_choice")
        try:
            navigation = tracker.get_slot("navigation")
        except:
            navigation = "NOBACK"
        print(f'Inside faq_text {value}')

        if navigation == "back3" or value.lower() == "back":
            return {"faq_text": None, "faq_choice": None, "navigation": None}
        else:
            # dispatcher.utter_template("utter_not_serving",tracker)
            print(f'checking navigation {faq_choice}')
            # if faq_choice!=INVALID_VALUE:
            if faq_choice != INVALID_VALUE:
                ques = value
                useNlp = True

                f = FAQ("./actionserver/controllers/faqs/test_faq.csv")
                # NLP disabled coz morethan 100 sec
                ans = f.ask_faq(ques, NLP=False)
                if ans:
                    dispatcher.utter_message(
                        "Your Question :{}\n Answer:{}".format(ques, ans))
                else:
                    dispatcher.utter_message("Query not found !")
                return {"faq_choice": faq_choice, "faq_text": None}
            else:
                {"faq_choice": faq_choice, "faq_text": "filled"}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        # handle back2 logic here
        dispatcher.utter_message("Faq is closed")
        # return greet_back(dispatcher)
        li = [SlotSet("faq_choice", None), SlotSet("faq_text", None)]
        li.extend(greet_back(dispatcher))
        return li
