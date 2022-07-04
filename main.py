import os
import cv2 as cv
import numpy
import numpy as np
from pgmpy.models import FactorGraph
from pgmpy.factors.discrete import DiscreteFactor
from pgmpy.inference import BeliefPropagation
import argparse


def get_histograms(box_list, img):  # function calculates histogram for every bounding box on current picture
    histogram_list = []
    for bbox in box_list:
        img_box = img[bbox[1]:bbox[1] + bbox[3], bbox[0]: bbox[0] + bbox[2]]
        # histogram consists of all 3 channels of BGR color space
        hist = cv.calcHist([img_box], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist = cv.normalize(hist, hist).flatten()
        histogram_list.append([bbox, hist])
    #     function returns a list of all histograms in a picture
    return histogram_list


def get_ratio(box_list):  # function calculates width - height ratio of every bounding box on current picture
    ratio_list = []
    for bbox in box_list:
        ratio = bbox[2]/bbox[3]
        ratio_list.append(ratio)
    #     function returns a list of ratios for all bounding boxes on current picture
    return ratio_list


def get_directory():  # acquiring directories from argument
    parser = argparse.ArgumentParser()
    parser.add_argument('folder_dir', type=str)
    args = parser.parse_args()
    folder_dir = args.folder_dir
    dirs = os.listdir(folder_dir)
    # loop looks for 'frames' folder and 'bboxes.txt' file
    for filename in dirs:
        if filename == 'frames':
            frames_path = os.path.join(folder_dir, filename)
        if filename == 'bboxes.txt':
            bboxes_path = os.path.join(folder_dir, filename)
    #     function returns a path for 'frames' folder and a path for 'bboxes.txt' file
    return frames_path, bboxes_path


def get_images(folder_path):  # function for creating a dictionary of photos
    images = {}
    dirs = os.listdir(folder_path)
    dirs.sort()
    for filename in dirs:
        img = cv.imread(os.path.join(folder_path, filename))
        if img is not None:
            # every image is keyed by its name
            images[filename] = img
    return images


def read_file(file_path):  # function for reading all lines of 'bboxes.txt'
    with open(file_path) as f:
        lines = f.readlines()
        # returns a list of text lines
        return lines


def operations(images, bboxes):
    key_list = []
    # creating a list that holds all keyes (image names)
    for key in images.keys():
        key_list.append(key)

    first_flag = False

    for line_no in range(len(bboxes)):
        # if a line of text is in key_list it is current image's name and the next line is the number of bounding boxes
        if bboxes[line_no].strip() in key_list:
            img_name = bboxes[line_no].strip()
            no = int(bboxes[line_no + 1].strip())
            img = images[img_name]
            # print(img_name)
            # print(no)

            # initiating lists for bounding boxes and their values
            boxes_now = []
            values_list = []
            # initiating FactorGraph()
            G = FactorGraph()

            for box in range(1, no + 1):
                values = bboxes[line_no + 1 + box].strip()
                values_list.append(values)
                values = values.split()
                # print(values)

                x = int(float(values[0]))
                y = int(float(values[1]))
                w = int(float(values[2]))
                h = int(float(values[3]))
                # print(x, y, w, h)

                # adding x,y coordinates and width, height of each bounding box of an image to a list
                boxes_now.append((x, y, w, h))

            # print(boxes_now)
            # check if there are bounding boxes on image
            if no > 0:
                # initiating the script for the first image in the folder
                if not first_flag:
                    # because it is the first image histograms and ratios are calculated as 'previous' variables in order
                    # for the script to work properly

                    previous_histograms = get_histograms(boxes_now, img)
                    previous_ratios = get_ratio(boxes_now)

                    # all people found on the first image will be new so a list of '-1' for every bounding box is created
                    # and printed
                    return_array = np.ones((len(previous_histograms)), dtype=numpy.int8)
                    return_array = return_array * -1
                    print(*return_array)

                    first_flag = True

                else:
                    # for the following pictures histograms and ratios are saved within 'current' variables, so they can be
                    # compared to values of the previous image

                    current_histograms = get_histograms(boxes_now, img)
                    current_ratios = get_ratio(boxes_now)

                    # probability_matrix is a matrix that will hold every probability of current bounding boxes being the
                    # same people that occurred in the previous picture
                    # rows of the matrix correspond to current picture and columns to the previous picture
                    probability_matrix = np.zeros((len(current_histograms), len(previous_histograms)))
                    # print(probability_matrix)

                    # this for loop fills the matrix with appropriate values
                    for cur in range(0, len(current_histograms)):
                        for prev in range(0, len(previous_histograms)):
                            histogram_probability = cv.compareHist(current_histograms[cur][1], previous_histograms[prev][1], cv.HISTCMP_CORREL)
                            ratio_probability = min([previous_ratios[prev], current_ratios[cur]]) / max([previous_ratios[prev], current_ratios[cur]])

                            # every value is a mean of probabilities based on histograms and ratios
                            probability_matrix[cur][prev] = (histogram_probability + ratio_probability) / 2
                            # print(probability_matrix[cur][prev])

                    # print(probability_matrix)

                    # adding a node to the graph for every bounding box in the current picture
                    for i in range(0, len(current_histograms)):
                        G.add_node(str(i))

                    # getting values of each probability from the matrix into a list
                    for i in range(0, len(current_histograms)):
                        prev_comp = []
                        for j in range(0, len(previous_histograms)):
                            prev_comp.append(probability_matrix[i][j])

                        # adding discrete factors for every node
                        # cardinality is one bigger than the amount of bounding boxes on the previous picture
                        # because it has to accommodate new people coming into the frame
                        # additional value to a list is a probability threshold for new people
                        df = DiscreteFactor([str(i)], [len(previous_histograms) + 1], [[0.75]+prev_comp])
                        G.add_factors(df)
                        G.add_edge(str(i), df)

                    # if there are more than bounding boxes on the current picture, factors and edges need to
                    # be added between them
                    if len(current_histograms) > 1:
                        nodes = []
                        for i in range(0, len(current_histograms)):
                            nodes.append(str(i))
                        # combination of names of every bounding box node
                        combinations = [(a, b) for idx, a in enumerate(nodes) for b in nodes[idx + 1:]]
                        # print(combinations)

                        # matrix that dictates dependencies between nodes
                        funny_matrix = np.ones((len(previous_histograms) + 1, len(previous_histograms) + 1))
                        for i in range(1, len(previous_histograms)+1):
                            funny_matrix[i][i] = 0
                        # print(funny_matrix)

                        # adding factors and edges
                        for pair in combinations:
                            df = DiscreteFactor([pair[0], pair[1]], [len(previous_histograms) + 1, len(previous_histograms) + 1], funny_matrix)
                            G.add_factors(df)
                            G.add_edge(pair[0], df)
                            G.add_edge(pair[1], df)

                    # initiating belief propagation and creating a dictionary of predictions
                    belief_propagation = BeliefPropagation(G)
                    belief_propagation.calibrate()
                    belief_dictionary = belief_propagation.map_query(G.get_variable_nodes(), show_progress=False)
                    # print(belief_dictionary)

                    # sorting and -1 subtraction of final values in order to comply with ground truth file
                    sorted_query = []
                    for key in sorted(belief_dictionary):
                        sorted_query.append(belief_dictionary[key]-1)
                    # printing final value for current image
                    print(*sorted_query)

                    # simple greedy search algorithm can be used for comparison with factor graph
                    end_flag = False
                    probability_array = np.zeros((len(current_histograms)))
                    return_array = np.ones((len(current_histograms)), dtype=numpy.int8)
                    return_array = return_array * -1
                    while not end_flag:
                        max_prob = np.amax(probability_matrix)
                        max_where = np.where(probability_matrix == max_prob)
                        max_row = max_where[0]
                        max_column = max_where[1]

                        probability_matrix[max_row, :] = 0
                        probability_matrix[:, max_column] = 0

                        if max_prob > 0.75:
                            return_array[max_row] = max_column
                            probability_array[max_row] = max_prob
                        elif max_prob == 0:
                            end_flag = True
                    # print("GREEDY: ", *return_array)

                    # at the end current histogram and ratio values are saved as 'previous' values
                    previous_histograms = current_histograms
                    previous_ratios = current_ratios
            # if not the next image will be treated the same as first image
            else:
                print()
                first_flag = False

            # cv.imshow('img', img)
            # cv.waitKey(0)
    # cv.destroyAllWindows()


if __name__ == '__main__':
    frames_path, bboxes_path = get_directory()
    images_dict = get_images(frames_path)
    bboxes_text = read_file(bboxes_path)
    operations(images_dict, bboxes_text)
