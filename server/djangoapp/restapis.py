import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    apikey = kwargs.get("apikey")
    try:
        if apikey:
            params = dict()
            params["text"] = kwargs.get("text")
            params["version"] = kwargs.get("version")
            params["features"] = kwargs.get("features")
            params["return_analyzed_text"] = kwargs.get("return_analyzed_text")
            
            response = requests.get(url, data=params, auth=HTTPBasicAuth('apikey', apikey), headers={'Content-Type': 'application/json'})
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(url, headers={'Content-Type': 'application/json'}, params=kwargs)
        
        # Check if the response contains valid JSON
        response.raise_for_status()  # This will raise an exception if the response status code is an HTTP error.
        json_data = response.json()
        return json_data
    except Exception as e:
        # Handle the exception and log or print an error message
        print(f"Error in get_request: {e}")
        return None

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(kwargs)
    print("POST to {} ".format(url))
    print(json_payload)
    url = "https://yinyinl33-5000.theiadocker-3-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/post_review"
    response = requests.post(url, params=kwargs, json=json_payload)
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    print(json_data)
    return response

# Create a get_dealers_from_cf method to get dealers from a cloud function
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result  
        # For each dealer object
        for dealer in dealers:
            # Access dictionary elements using keys
            address = dealer.get("address")
            city = dealer.get("city")
            full_name = dealer.get("full_name")
            id = dealer.get("id")
            lat = dealer.get("lat")
            long = dealer.get("long")
            short_name = dealer.get("short_name")
            st = dealer.get("st")
            zip = dealer.get("zip")
            # Create a CarDealer object using these values
            dealer_obj = CarDealer(address=address, city=city, full_name=full_name, id=id, lat=lat, long=long,
                                   short_name=short_name, st=st, zip=zip)
            results.append(dealer_obj)
    return results

def get_dealer_by_id_from_cf(url, id, **kwargs):
    result = {}
    # Call get_request with a URL parameter
    json_result = get_request(url, id=id)
    if json_result:
        # Get the row list in JSON as dealers
        #dealers = json_result["rows"]
        dealers = json_result  
        # For each dealer object
        dealer = dealers[0]
        # Create a CarDealer object with values in `doc` object
        dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                short_name=dealer["short_name"],
                                st=dealer["st"], zip=dealer["zip"])
        result = dealer_obj
    return result

def get_dealers_by_state_from_cf(url, state, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, state=state)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["rows"]
        # For each dealer object
        for dealer in dealers:
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                   id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                   short_name=dealer["short_name"],
                                   st=dealer["st"], zip=dealer["zip"])
            results.append(dealer_obj)
    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    id = kwargs.get("id")
    if id:
        json_result = get_request(url, id=id)
    else:
        json_result = get_request(url)
    print(json_result, "96")
    if json_result:
        if isinstance(json_result, list):  # Check if json_result is a list
            reviews = json_result
        else:
            reviews = json_result["data"]["docs"]

        # Check if 'reviews' is a list of one dictionary
        if isinstance(reviews, list) and len(reviews) == 1 and isinstance(reviews[0], dict):
            reviews = reviews[0]

        for dealer_review in reviews:
            print("dealer_review--------------------", dealer_review)  # Print dealer_review
            if isinstance(dealer_review, str):  # Check if dealer_review is a string
                try:
                    dealer_review = json.loads(dealer_review)
                except json.JSONDecodeError:
                    continue  # Skip this iteration if the JSON decoding fails

            review_obj = DealerReview(
                dealership=dealer_review.get("dealership"),
                name=dealer_review.get("name"),
                purchase=dealer_review.get("purchase"),
                review=dealer_review.get("review"),
                purchase_date=dealer_review.get("purchase_date"),
                car_make=dealer_review.get("car_make"),
                car_model=dealer_review.get("car_model"),
                car_year=dealer_review.get("car_year"),
                sentiment='',
                id=dealer_review.get("id")
            )

            sentiment = analyze_review_sentiments(review_obj.review)
            print(sentiment)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(dealer_review):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
    apikey = "ViIC78QbeRRdyj5snFTVcw0V_A9hajV0gd7mCqz1yBCF"
    url = "https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/940ea83d-0662-4ce1-9248-9679d95d8bb6"
    
    authenticator = IAMAuthenticator(apikey)
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2022-04-07',
        authenticator=authenticator
    )

    natural_language_understanding.set_service_url(url)

    response = natural_language_understanding.analyze(
        text=dealer_review,
        language='en',
        features=Features(sentiment=SentimentOptions(targets=[dealer_review]))
    ).get_result()

    print(json.dumps(response, indent=2))
    
    return response["sentiment"]["document"]["label"]