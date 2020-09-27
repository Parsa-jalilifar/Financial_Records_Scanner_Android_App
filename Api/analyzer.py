
import os
import cv2
import pytesseract
import pandas as pd
import numpy as np
import concurrent.futures
from pytesseract import Output
from googlemaps import Client as client
from PIL import Image

######### Required Image processing Functions ##############

#get grayscale 
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#get inverse grascale
def get_inverse_grayscale(image):
    return cv2.bitwise_not(image)

#noise removal
def remove_noise(image):
    return cv2.medianBlur(image,5)
 
#thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

##Adaptive Gaussian Thresholding
def Adaptive_thresholding(image):
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)    

#dilation
def dilate(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.dilate(image, kernel, iterations = 1)
    
#erosion
def erode(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.erode(image, kernel, iterations = 1)

#opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

#canny edge detection
def canny(image):
    return cv2.Canny(image, 100, 200)

#Median Blur
def blur_median(image):
    return cv2.medianBlur()

#Gaussian Blurring
def blur_gaussian(image):
    return cv2.GaussianBlur(image,(5,5),0)

#Bilateral Filtering
def Bilateral(image):
    return cv2.BilateralFilter(img,9,75,75)

#skew correction
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

#template matching
def match_template(image, template):
    return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED) 

############## Image Conversions ##############

class Extractor():

  __API_KEY = 'AIzaSyDSN-u7kK05H45CZLTnl6h9vFnCy9EMxnw' 
  __JSON_PATH = './json_documents'
  __IMAGE_PATH = './test_images' 
  __UF_DATA_PATH = './extraction_data'

  def __init__(self):
       
     Extractor.__data_DICT = []  
     Extractor.__custom_config = r'--oem 3 -- psm 6 outputbase digits'

  def __is_number(n):
     try:
         float(n)   
     except ValueError:
         return False
     return True

  def get_resultant(self): 
     return Extractor.__data_DICT             

  def start_EXTRACTION(self):
      # Multiprocessing
     img_ID_LIST = os.listdir(Extractor.__IMAGE_PATH)[:]
     with concurrent.futures.ProcessPoolExector() as executor:
        extracton_STATUS_LIST = executor.map(Extractor.__extraction_ROUTINE, img_ID_LIST)
     
  def __extraction_ROUTINE(img_ID):
   
    i = 0
    while True:
       Extractor.__OCR_ROUTINE_DEFAULT(img_path = __IMAGE_PATH + '/' + img_ID, scale_percent = 100 + i)
  
       if Extractor.__extract_DATA(img_ID) is not False: 
            return Extractor.__extract_DATA(img_ID)
       elif i < 20:
            i += 10
       elif i >= 20 and i < 30:
            i += 5
       elif i == 30:
            break
    Extractor.__data_DICT[img_ID[:-4]] = None            
      
  def __extract_DATA(img_test_ID):
       
     total_cost_LC = None
     tax_amount_LC = None
     purchase_date_LC = None
     business_name_LC = None
     category_LC = None
     query_info_LC = []
     
     data_path = "./extraction_data/" + img_test_ID + "_RTD.txt"
     text_data = open(data_path, 'r')
     data_list = text_data.readlines()  
     
     for line in data_list: 
        # Extract Receipt Cost
        match_Total = re.search(r'\bTotal\b', line) or re.search(r'\bTOTAL\b', line)
        if (match_Total != None):
                        
            for word in line.split():
                if word.startswith('$') and is_number(word[1:]): 
                   total_cost_LC = float(word[1:])
                   break
                elif is_number(word):
                   total_cost_LC = float(word)   
                   break 

        #Extract Tax Amount
        match_Tax = re.search(r'\bTax\b', line) or re.search(r'\bTAX\b', line)
        if (match_Tax != None):

            for word in line.split():
                if (word.startswith('$') and is_number(word[1:])):
                   tax_amount_LC = float(word[1:])
                   break
                elif is_number(word):
                   tax_amount_LC = float(word)
                   break

        #Extract Date of Purchase
        match_Date = re.search(r'\b(1[0-2]|0[1-9])-(3[01]|[12][0-9]|0[1-9])-[0-9]{4}\b', line)
        if (match_Date != None):
            for word in line.split():
                if (re.match(r'\b(1[0-2]|0[1-9])-(3[01]|[12][0-9]|0[1-9])-[0-9]{4}\b', word)):
                   purchase_date_LC = word
                   break

        #Extract Business Phone Number
        Match_Phone = re.search(r'\b\d{3}-\d{3}-\d{4}\b', line) or re.search(r'\b[(]\d{3}[)][ ]*\d{3}-\d{4}\b', line)
        if (Match_Phone != None):           
            for word in line.split():
                if (re.match(r'\b\d{3}-\d{3}-\d{4}\b', word)):
                   query_info_LC = query_INFO(word)[:]
                   break
                elif (re.match(r'\b[(]\d{3}[)][ ]*\d{3}-\d{4}\b', word)):
                   query_info_LC = query_INFO(word)[:]
                   break
        
        if total_cost_LC == None or tax_amount_LC == None or purchase_date_LC == None or len(query_INFO) == 0:
            return False
        else:
            business_name_LC = query_info_LC[0]
            category_LC = query_info_LC[1]

            Extractor.__data_DICT[img_test_ID[:-4]] = [
               purchase_date_LC, 
               business_name_LC,
               category_LC,
               tax_amount_LC,
               total_cost_LC,
            ]
            return True
   
  def __query_INFO(search_parameter):
    
     gmaps = client(key = Extractor.__API_KEY)
     #Query google API by parameter_type  
     query_results = client.find_place(gmaps, ('+1' + search_parameter) , 'phonenumber', ['name', 'types'])        
     for item in query_results.items():
        query_DATA.append(item[1][0]['name'])
        query_DATA.append(item[1][0]['types'][0]) 
        return query_DATA

  def __OCR_ROUTINE_DEFAULT(img_ID, scale_percent):    

     TEST_IMG_PATH =  './test_images/' + img_ID  + '_TI.jpg'
         
     # Modify DPI 
     receiptIMG = Image.open(img_ID)
     receiptIMG.save(TEST_IMG_PATH, dpi = (300,300))
     img_modified = cv2.imread(TEST_IMG_PATH)
     os.remove(TEST_IMG_PATH)

     # Modify Size
     width = int(img_modified.shape[1] * scale_percent / 100)
     height = int(img_modified.shape[0] * scale_percent / 100)
     dim = (width, height)
     resized = cv2.resize(img_modified, dim, interpolation = cv2.INTER_AREA) 

     # Convert to Grayscale
     gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
     
     # Binarize
     thresholded = thresholding(gray)

     # deskew
     deskewed = deskew(thresholded)
       
     # execute tesseract-OCR
     data = pytesseract.image_to_string(deskewed, config=Extractor.custom_config)
     data_file = open("./extraction_data/" + img_ID + "_RTD.txt", "w")
     n = data_file.write(data)
     data_file.close()
   
  def __OCR_ROUTINE_INVERSE(img_ID, scale_percent):
       print('inverse routine called')

  def __OCR_ROUTINE_BLUR(img_ID, scale_percent):
       print('blur rountine called')        




















   


   




  


