#!/usr/bin/env python
# coding: utf-8

# In[1]:


import boto3
import json
import urllib.parse
import urllib.request
import pandas as pd


# In[2]:


def get_data(total_num, category):
    num = 0
    offset = 0
    
    while num < total_num:
        param = {"categories": category, "location": "Manhattan", "offset": offset, "limit": 50}
        param = urllib.parse.urlencode(param)
        url = 'https://api.yelp.com/v3/businesses/search'
        url = "?".join([url, param])
        # print(url)
        # print(num)
        headers = {"Authorization": "Bearer "
                                    ""}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = response.read()
        data = json.loads(data)
        if not data["businesses"]:
            break
        for item in data["businesses"]:
            if item["id"] in restaurant_id:
                continue
            else:
                restaurant_id.append(item["id"])
                names.append(item["name"])
                restaurant_type.append(category)
                address.append(item["location"]["address1"])
                latitude.append(item["coordinates"]["latitude"])
                longitude.append(item["coordinates"]["longitude"])
                num_of_reviews.append(item["review_count"])
                rating.append(item["rating"])
                zip_code.append(item["location"]["zip_code"])
                num += 1
                if num == total_num:
                    break
        offset += 50
        if offset > 950:
            break
    print('retrived ',num,'results')


# In[3]:


def get_json(total_num, category,last,jsn):
    num = 0
    offset = 0
    
    while num < total_num:
        param = {"categories": category, "location": "Manhattan", "offset": offset, "limit": 50}
        param = urllib.parse.urlencode(param)
        url = 'https://api.yelp.com/v3/businesses/search'
        url = "?".join([url, param])
        # print(url)
        # print(num)
        headers = {"Authorization": "Bearer "
                                    ""}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = response.read()
        data = json.loads(data)
        if not data["businesses"]:
            break
        for item in data["businesses"]:
            if item["id"] in restaurant_id:
                continue
            else:
                restaurant_id.append(item["id"])
                temp = {"index": {"_index": category, "_id": last+num+1}}
                jsn += json.dumps(temp)
                jsn += '\n'
                temp = {"restaurant_id": item["id"]}
                jsn += json.dumps(temp)
                jsn += '\n'
                num += 1
                if num == total_num:
                    break
        offset += 50
        if offset > 950:
            break
    print('retrived ',num,'results')
    return jsn


# In[4]:


def save_to_s3(filename):
    from io import BytesIO

    session = boto3.Session(
    aws_access_key_id='',
    aws_secret_access_key=''
    )
    s3 = session.resource('s3')

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer)
    content = csv_buffer.getvalue()
    obj = s3.Object('yelp-restaurants-information', filename)
    result = obj.put(Body=content)


# In[29]:


restaurant_id = []
names = []
restaurant_type = []
address = []
latitude = []
longitude = []
num_of_reviews = []
rating = []
zip_code = []


# **Scrap JSON Results**

# In[21]:


jsn = get_json(1000,'chinese',0,'')


# In[22]:


jsn = get_json(1000,'tradamerican',1000,jsn)


# In[23]:


jsn = get_json(1000,'italian',1999,jsn)


# In[24]:


jsn = get_json(1000,'japanese',2985,jsn)


# In[25]:


jsn = get_json(1000,'mexican',3945,jsn)


# In[26]:


jsn = get_json(1000,'indpak',4926,jsn)


# In[27]:


print(jsn)


# In[28]:


fh = open('restaurants.txt', 'w', encoding='utf-8')
fh.write(jsn)
fh.close


# **Scrap DF Results

# In[108]:


get_data(1000,'chinese')


# In[244]:


get_data(1000,'tradamerican')


# In[245]:


get_data(1000,'italian')


# In[246]:


get_data(1000,'japanese')


# In[247]:


get_data(1000,'mexican')


# In[248]:


get_data(1000,'indpak')


# In[249]:


df = pd.DataFrame({"restaurant_id":restaurant_id,"names":names,"restaurant_type":restaurant_type,
                   "address":address,"latitude":latitude,"longitude":longitude,"num_of_reviews":num_of_reviews,
                   "rating":rating,"zip_code":zip_code})


# In[250]:


save_to_s3('restaurants.csv')


# In[251]:


df


# In[ ]:





# In[ ]:




