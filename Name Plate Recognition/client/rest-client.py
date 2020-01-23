from __future__ import print_function
import requests
import json
import sys
import base64

host_ip = sys.argv[1]
method = sys.argv[2]
video_id = sys.argv[3]


if method == "PUT":
    try:
        addr = 'http://'+host_ip+':5000'
        headers = {'content-type': 'application/json'}
        #print(addr)
        #print(filename)
        #img = open(filename, 'rb').read()
        # send http request with image and receive response
        url = addr + '/predict'

        #image_val = base64.encodebytes(img)
        #image_val = image_val.decode('ascii')

        requestBody = {'videoid': video_id}
        response = requests.put(url, data=json.dumps(requestBody), headers=headers)
        #print("Response is:", response)
        data = json.loads(response.text)
        #value = data['original_likes:predicted_likes']
        print("Title:", data['title'])
        print("Video id: "+ video_id)
        print("Predicted Likes: "+data['predicted_likes'])
        print("Original Likes: "+data['original_likes'])
        print("Difference: ", int(data['predicted_likes'])-int(data['original_likes']))
        print("Error Rate: ", ((100*(int(data['predicted_likes'])-int(data['original_likes'])))/int(data['original_likes'])))
    except Exception as e:
        print(e)

else:
    print("yet to implement:")
