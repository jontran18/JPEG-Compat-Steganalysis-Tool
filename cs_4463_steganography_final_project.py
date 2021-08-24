# -*- coding: utf-8 -*-
"""CS 4463 - Steganography Final Project

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MIvPOVpVsJB7QlNUd2PngaBNi_mXIxgl

CS 4463 - Steganography Final Project
"""

# Authors: Zackery Weik, Dayne Closser, Jonathon Tran

# User Guide: Run the program and specify the name of your input image when prompted
# Program will check the input image for JPEG Compatibility and print out relevant data
# A CSV file is generated at the end of the program containing the quantization table data

from PIL import Image
import numpy as np
import math
import sys
import csv

# Declare block dimensions
block_height = block_width = 8

# Square root of 2
sqr_2 = math.sqrt(2)

# Array to hold all dct values
dct_all = []
# Creates basis matrix
def generate_basis():
  basis_array = np.empty([8,8,8,8])
  for u in range(8):
    for v in range(8):
      for x in range(8):
        for y in range(8):
          basis_array[u,v,x,y] = math.cos((math.pi*u*(2*x+1))/16) * math.cos((math.pi*v*(2*y+1))/16)
  return basis_array

# Generates pre-quantized DCTs | Little d(k)
def generate_DCTs(basis_array, pixel_values):
  dct_array = np.zeros([8,8])
  for u in range(8):
    for v in range(8):
      for x in range(8):
        for y in range(8):
          dct_array[u,v] += basis_array[u,v,x,y] * (pixel_values[x,y] - 128)
      if u == 0:
        dct_array[u,v] *= 1/sqr_2
      if v == 0:
        dct_array[u,v] *= 1/sqr_2
      dct_array[u,v] /= 4
  dct_all.append(dct_array)
  return dct_array

# Quantizes DCTs | Big D(k)
def quantize(dct_array, Q_table):
  quantized_dct = np.empty([8,8])
  for x in range(8):
    for y in range(8):
      quantized_dct[x,y] = round(dct_array[x,y] / Q_table[x,y])
  return quantized_dct

# Dequantizes values | QD
def dequantize(quantized_dct, Q_table):
  dequantized_dct = np.empty([8,8])
  for x in range(8):
    for y in range(8):
      dequantized_dct[x,y] = quantized_dct[x,y] * Q_table[x,y]
  return dequantized_dct

# The inverse DCT function | B raw
def inverse_DCTs(basis_array, dequantized_dct):
  inverse_dct = np.zeros([8,8])
  for u in range(8):
    for v in range(8):
      for x in range(8):
        for y in range(8):
          inverse_dct[u,v] += basis_array[u,v,x,y] * dequantized_dct[x,y]
          if u == 0:
            inverse_dct[u,v] *= (1/sqr_2)
          if v == 0:
            inverse_dct[u,v] *= (1/sqr_2)
      inverse_dct[u,v] /= 4
  return inverse_dct

# Round the inverse DCT values | B
def round_table(inverse_dct):
  rounded_inverse = np.empty([8,8])
  for u in range(8):
    for v in range(8):
      if inverse_dct[u,v] < 0:
        rounded_inverse[u,v] = 0
      elif inverse_dct[u,v] > 255:
        rounded_inverse[u,v] = 255
      else:
        rounded_inverse[u,v] = round(inverse_dct[u,v])
  return rounded_inverse

# Round the inverse DCT values | B (signed values)
def round_signed(inverse_dct):
  rounded_inverse = np.empty([8,8])
  for u in range(8):
    for v in range(8):
      if inverse_dct[u,v] < -128:
        rounded_inverse[u,v] = -128
      elif inverse_dct[u,v] > 127:
        rounded_inverse[u,v] = 127
      else:
        rounded_inverse[u,v] = round(inverse_dct[u,v])
  return rounded_inverse

# Calculates S values
def calculate_s(Q_table, QD_Prime):
  s_value = 0
  for x in range(8):
    for y in range(8):
      s_value += abs(QD_Prime[x,y] - Q_table[x,y] * round(QD_Prime[x,y] / Q_table[x,y]))
  return s_value

# Different equation to calculate S values
def calculate_s_2(inverse_dct, rounded_inverse):
  s_value = 0
  for u in range(8):
    for v in range(8):
      s_value += math.pow(rounded_inverse[u,v] - inverse_dct[u,v], 2)
  return s_value  

# No truncation!
np.set_printoptions(threshold=sys.maxsize)
np.set_printoptions(suppress=True)

# Open image
img = Image.open(input("Please enter the image file name: "))

# Checking to see if the image is 8 bit greyscale
if img.mode != 'L':
    sys.exit("Not a grayscale image")
img = np.asarray(img)

# Get image dimensions then reduce to dimensions evenly divisible by 8
img_height, img_width = img.shape
if img_height % 8 != 0 and img_height > 8:
  img_height = img_height - (img_height % 8)
if img_width % 8 != 0 and img_width > 8:
  img_width = img_width - (img_width % 8)
img = img[0:img_height, 0:img_width]

print("The trimmed image dimensions are ")
print(img.shape)

# Create 4D array of 8x8 blocks
block_array = img.reshape(img_height // block_height, block_height, img_width // block_width, block_width)
block_array = block_array.swapaxes(1,2)

# Remove saturated blocks
unsaturated_blocks = []
for i in block_array:
  for j in i:
    isUnsaturated = True
    for k in j:
      for x in k:
        if x==0 or x==255:
          isUnsaturated = False
      if isUnsaturated == False:
        break
    if isUnsaturated == True:
      unsaturated_blocks.append(j)

print("The total number of unsaturated blocks is ")
print(len(unsaturated_blocks))
basis_array = generate_basis()

# Hardcoded Q table for test images
Q_table = np.array([[1,1,1,1,1,1,1,1],
                    [1,1,1,1,1,1,1,1],
                    [1,1,1,1,1,1,1,1],
                    [1,1,1,1,1,1,1,1],
                    [1,1,1,1,2,2,1,1],
                    [2,1,1,1,2,2,2,2],
                    [2,2,2,2,2,1,2,2],
                    [2,2,2,2,2,2,2,2]])

#Q_table = np.array([[6,4,5,6,5,4,6,6,],
#                    [5,6,7,7,6,8,10,16],
#                    [10,10,9,9,10,20,14,15],
#                    [12,16,23,20,24,24,23,20],
#                    [22,22,26,29,37,31,26,27],
#                    [35,28,22,22,32,44,32,35],
#                    [38,39,41,42,41,25,31,45],
#                    [48,45,40,48,37,40,41,40]])

# create array to hold all blocks that are compatible with JPEG compression
compatible_blocks = []

for x in unsaturated_blocks:
  # Find all unquantized DCT coefficients
  dct_array = generate_DCTs(basis_array, x)
  # Quantize DCT coefficients
  quantized_dct = quantize(dct_array, Q_table)
  # Dequantize DCT coefficients similar to JPEG decompression
  dequantized_dct = dequantize(quantized_dct, Q_table)
  # Inverse the dequantized DCT coefficients similar to JPEG decompression
  inverse_dct = inverse_DCTs(basis_array, dequantized_dct)
  # Round the DCT coefficients to the nearest integer
  rounded_inverse = round_signed(inverse_dct)
  # Calculate data loss and compare to acceptable loss by JPEG compression
  s_value = calculate_s_2(inverse_dct, rounded_inverse)
  if s_value <= 16:
    compatible_blocks.append(x)
print("Number of blocks compatible with JPEG Compression ")
print(len(compatible_blocks))

# Create array to hold all q testing values
q_output = np.zeros((8,8,100))
# Algorithm to test 100 q values for local minima
for u in range(8):
  for v in range(8):
    for q in range(1,100):
      for x in dct_all:
        q_output[u,v,q] += abs(x[u,v] - q * round(x[u,v]/q))
      q_output[u,v,q] *= 1/len(dct_all)
print(q_output[7,7])

#Write all q testing values to a csv file
with open('q_table_output.csv', 'w', newline='') as csvfile:
  write = csv.writer(csvfile, delimiter=',')
  for x in range(8):
    for y in range(8):
      write.writerow(q_output[x][y])