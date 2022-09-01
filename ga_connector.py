import logging    # These are necessary libraries we are importing
import json
from sanic import Blueprint, response
from sanic.request import Request
from typing import Text, Optional, List, Dict, Any

from rasa.core.channels.channel import UserMessage, OutputChannel
from rasa.core.channels.channel import InputChannel
from rasa.core.channels.channel import CollectingOutputChannel

logger = logging.getLogger(__name__)

class GoogleConnector(InputChannel):
    """A custom http input channel.
    This implementation is the basis for a custom implementation of a chat
    frontend. You can customize this to send messages to Rasa Core and
    retrieve responses from the agent."""

    @classmethod
    def name(cls):
        return "google_assistant"


    def blueprint(self, on_new_message):                        # Here, we define the webhook that Google Assistant 
                                                                # will use to pass the user inputs to Rasa Core,    
        google_webhook = Blueprint('google_webhook', __name__)  # collect the responses and send them to Google Assistant

        @google_webhook.route("/", methods=['GET'])          
        async def health(request):                           # We design a Health route to control the connection 
            return response.json({"status": "ok"})           # is established by returning 200 ok message

        @google_webhook.route("/webhook", methods=['POST'])
        async def receive(request):                          # Then we define the main route for our purpose
            payload = request.json	
            intent = payload['inputs'][0]['intent'] 			
            text = payload['inputs'][0]['rawInputs'][0]['query'] 
            
            if intent == 'actions.intent.MAIN':	 #This is the initial message we ask to recieve when the assitant is invoked
                message = "Hello! If you want to know what I can do, ask: help. If you are ready, tell me: I want to order pizza." 			 
            else:
                out = CollectingOutputChannel()			
                await on_new_message(UserMessage(text, out))
                responses = [m["text"] for m in out.messages]
                # message = responses[0]
                message = "\n".join(responses)  # I want to show all the "dispatcher.utter_message"
            r = {
                  "expectUserResponse": 'true',
                  "expectedInputs": [
                    {
                      "possibleIntents": [
                        {
                          "intent": "actions.intent.TEXT"   #This is our second intent defined in action.json, remember?
                        }
                    ],
                    "inputPrompt": {
                      "richInitialPrompt": {
                        "items": [
                          {
                            "simpleResponse": {
                              "textToSpeech": message,
                              "displayText": message
                              }
                            }
                          ]
                        }
                      }
                    }
                  ]
                }
            return response.json(r)				
        return google_webhook
