"""norm_cent.py: normalize over all files from each folder of an directory
- read keypoints from each folder from an directory and write them into a dictionary
- compute the mean and stdev of each value
- use the mean and stdev to normalize the data and write them into new json, repeat for all folders

VERSION DESCRIPTION:
- sticked to row per row and transpose

"""

import json
import numpy as np
import os
import statistics
from pathlib import Path
import sys
import time


# TODO: save as centralized dictioanry
# TODO: save final conetralzed and normalized result as dictioanry, no files as output anymore

class Normalize:

    def __init__(self, path_to_json_dir, path_to_target_dir):
        self.path_to_json = path_to_json_dir
        self.path_to_target_dir = path_to_target_dir
        self.keys = ['pose_keypoints_2d', 'face_keypoints_2d', 'hand_left_keypoints_2d', 'hand_right_keypoints_2d']

    def main(self):
        # create folders and paths
        data_dir_origin, data_dir_target, subdirectories = self.create_folders()

        # read files to dictionary and save dictionary in target directory
        dictionary_file_path = self.copy_dictionary_to_file(data_dir_origin, data_dir_target, subdirectories)

        # centralize values
        all_files_dictionary_centralized = None
        all_files_dictionary_centralized = self.centralize(data_dir_origin, data_dir_target, subdirectories, dictionary_file_path)
        # print(all_files_dictionary_centralized)
        # normalize values
        all_mean_stdev, keys = self.normalize(data_dir_origin, data_dir_target, subdirectories, dictionary_file_path, all_files_dictionary_centralized)
        # self.normalize_write(all_mean_stdev, data_dir_origin, data_dir_target, keys, subdirectories)

    def create_folders(self):
        # get subdirectories of the path
        subdirectories = [x[1] for x in os.walk(self.path_to_json)]
        data_dir_origin = Path(self.path_to_json)
        subdirectories = subdirectories[0]

        if self.path_to_target_dir == "":
            data_dir_target = data_dir_origin.parent / str(data_dir_origin.name + "_normalized")
        else:
            data_dir_target = Path(self.path_to_target_dir)

        # create new target directory, the files will be saved there
        if not os.path.exists(data_dir_target):
            os.makedirs(data_dir_target)

        for subdir in subdirectories:
            if not os.path.exists(data_dir_target / subdir):
                os.makedirs(data_dir_target / subdir)

        return data_dir_origin, data_dir_target, subdirectories

    def copy_dictionary_to_file(self, data_dir_origin, data_dir_target, subdirectories):

        dictionary_file_path = data_dir_target / 'all_files.npy'
        last_folder = os.path.basename(os.path.normpath(dictionary_file_path.parent)) + "/" + str(dictionary_file_path.name)

        if dictionary_file_path.is_file():
            print(".../%s file already exists. Not copying files " % last_folder)
            return dictionary_file_path
        else:
            print("Saving files to %s " % dictionary_file_path)

        # use keys of openpose here
        all_files = {}

        for subdir in subdirectories:
            print("Reading files from %s" % subdir)
            json_files = [pos_json for pos_json in os.listdir(data_dir_origin / subdir)
                          if pos_json.endswith('.json')]
            all_files[subdir] = {}
            # load files from one folder into dictionary
            for file in json_files:
                temp_df = json.load(open(data_dir_origin / subdir / file))
                all_files[subdir][file] = temp_df

        np.save(dictionary_file_path, all_files)
        return Path(dictionary_file_path)

    def centralize(self, data_dir_origin, data_dir_target, subdirectories, dictionary_file_path):

        # load from .npy file
        print("To centralize load file from \n %s" % dictionary_file_path)
        old = np.load
        np.load = lambda *a, **k: old(*a, **k, allow_pickle=True)
        all_files_dictionary = np.load(dictionary_file_path).item()

        # used keys of openpose here
        keys = self.keys
        folder_keys = {'pose_keypoints_2d': [], 'face_keypoints_2d': [], 'hand_left_keypoints_2d': [],
                       'hand_right_keypoints_2d': []}

        for subdir in subdirectories:
            # json_files = [pos_json for pos_json in os.listdir(data_dir_origin / subdir)
            #               if pos_json.endswith('.json')]

            all_files = {}

            # load files from one folder into dictionary
            for file in all_files_dictionary[subdir]:
                temp_df = all_files_dictionary[subdir][file]
                # print(temp_df)
                all_files[file] = {}
                once = 1
                # init dictionaries & write x, y values into dictionary
                for k in keys:
                    all_files[file][k] = {'x': [], 'y': []}
                    all_files[file][k]['x'].append(temp_df['people'][0][k][0::3])
                    all_files[file][k]['y'].append(temp_df['people'][0][k][1::3])
                    temp_c = temp_df['people'][0][k][2::3]
                    results_x = []
                    results_y = []
                    x_in_key = all_files[file][k]['x'][0]
                    y_in_key = all_files[file][k]['y'][0]

                    # set neck once
                    if once == 1:
                        neck_zero_x = all_files[file][k]['x'][0][0]
                        neck_zero_y = all_files[file][k]['y'][0][0]
                        once = 0

                    # compute for pose
                    if k == "pose_keypoints_2d":
                        results_x.append(0)
                        results_y.append(0)
                        # start with 1 -> element 0 is neck
                        # get upper body
                        for idx in range(1, len(x_in_key[:9])):
                            if x_in_key[idx] == 0:
                                results_x.append('Null')
                            else:
                                results_x.append(neck_zero_x - x_in_key[idx])

                            if y_in_key[idx] == 0:
                                results_y.append("Null")
                            else:
                                results_y.append(neck_zero_y - y_in_key[idx])

                        # add Null as legs
                        results_x += (['Null'] * 6)
                        results_y += (['Null'] * 6)

                        for idx in range(15, len(x_in_key[:19])):
                            if x_in_key[idx] == 0:
                                results_x.append('Null')
                            else:
                                results_x.append(neck_zero_x - x_in_key[idx])

                            if y_in_key[idx] == 0:
                                results_y.append("Null")
                            else:
                                results_y.append(neck_zero_y - y_in_key[idx])

                        # add more legs
                        results_x += (['Null'] * 6)
                        results_y += (['Null'] * 6)

                        values = []
                        for index in range(len(temp_c)):
                            values.append(results_x[index])
                            values.append(results_y[index])
                            values.append(temp_c[index])
                        temp_df['people'][0][k] = values
                    else:
                        # start with 1 -> element 0 is neck
                        # get upper body
                        for idx in range(0, len(x_in_key)):
                            if x_in_key[idx] == 0:
                                results_x.append('Null')
                            else:
                                results_x.append(neck_zero_x - x_in_key[idx])

                            if y_in_key[idx] == 0:
                                results_y.append("Null")
                            else:
                                results_y.append(neck_zero_y - y_in_key[idx])

                        values = []
                        for index in range(len(temp_c)):
                            values.append(results_x[index])
                            values.append(results_y[index])
                            values.append(temp_c[index])
                        temp_df['people'][0][k] = values

                all_files_dictionary[subdir][file] = temp_df

                # ## Save our changes to JSON file
                # jsonFile = open(data_dir_target / subdir / file, "w+")
                # jsonFile.write(json.dumps(temp_df))
                # jsonFile.close()
            # print("%s done" % subdir)
        print("centralization done")

        dictionary_file_path = data_dir_target / 'all_files_centralized.npy'
        last_folder = os.path.basename(os.path.normpath(dictionary_file_path.parent)) + "/" + str(dictionary_file_path.name)

        if dictionary_file_path.is_file():
            print(".../%s already exists. Not saving centralized data " % last_folder)
            return all_files_dictionary
        else:
            print("Saving centralized results to %s " % last_folder)
            np.save(dictionary_file_path, all_files_dictionary)

        return all_files_dictionary

    def normalize(self, data_dir_origin, data_dir_target, subdirectories, dictionary_file_path, all_files_dictionary_centralized):

        if all_files_dictionary_centralized is None:
            # load from .npy file
            print("To normalize loading from %s file" % dictionary_file_path)
            old = np.load
            np.load = lambda *a, **k: old(*a, **k, allow_pickle=True)
            all_files_dictionary = np.load(dictionary_file_path).item()
        else:
            all_files_dictionary = all_files_dictionary_centralized


        # use keys of openpose here
        keys = self.keys
        all_mean_stdev = {}  # holds means and stdev of each directory, one json file per directory
        once = 1
        all_files_xy = {'all': {}}
        mean_stdev_x = []
        mean_stdev_y = []

        for subdir in subdirectories:
            print("Reading files from %s" % subdir)
            # json_files = [pos_json for pos_json in os.listdir(data_dir_origin / subdir)
            #               if pos_json.endswith('.json')]

            # load files from one folder into dictionary
            for file in all_files_dictionary[subdir]:
                temp_df = all_files_dictionary[subdir][file]
                if once == 1:
                    for k in keys:
                        all_files_xy['all'][k] = {'x': [], 'y': []}
                    once = 0
                for k in keys:
                    all_files_xy['all'][k]['x'].append(temp_df['people'][0][k][0::3])
                    all_files_xy['all'][k]['y'].append(temp_df['people'][0][k][1::3])
        print("Files read, computing mean and stdev")

        # print(all_files_xy)

        for k in keys:
            for list in np.array(all_files_xy['all'][k]['x']).T.tolist():
                # print(list)
                if "Null" in list:
                    mean_stdev_x.append(["Null", "Null"])
                else:
                    list = [float(item) for item in list]
                    mean_stdev_x.append([np.mean(list), statistics.pstdev(list)])

            for list in np.array(all_files_xy['all'][k]['y']).T.tolist():
                if "Null" in list:
                    mean_stdev_y.append(["Null", "Null"])
                else:
                    list = [float(item) for item in list]
                    mean_stdev_y.append([np.mean(list), statistics.pstdev(list)])

            all_mean_stdev[k] = [np.array(mean_stdev_x).T.tolist(), np.array(mean_stdev_y).T.tolist()]

        # write the computed means and std_dev into json file
        f = open(data_dir_target / "dir_mean_stdev.json", "w")
        f.write(json.dumps(all_mean_stdev))
        f.close()

        return all_mean_stdev, keys

    def normalize_write(self, all_mean_stdev, data_dir_origin, data_dir_target, subdirectories):
        # use mean and stdev to compute values for the json files
        keys = self.keys
        for subdir in subdirectories:
            json_files = [pos_json for pos_json in os.listdir(data_dir_origin / subdir)
                          if pos_json.endswith('.json')]

            for file in json_files:
                jsonFile = open(data_dir_origin / subdir / file, "r")  # Open the JSON file for reading
                data = json.load(jsonFile)  # Read the JSON into the buffer
                jsonFile.close()  # Close the JSON file

                # x -> [0::3]
                # y -> [1:.3]
                # c -> [2::3] (confidence)
                for k in keys:
                    # x values
                    temp_x = data['people'][0][k][0::3]
                    temp_y = data['people'][0][k][1::3]
                    temp_c = data['people'][0][k][2::3]

                    # get x values and normalize it
                    for index in range(len(temp_x)):
                        mean_x = all_mean_stdev[k][0][0][index]
                        stdev_x = all_mean_stdev[k][0][1][index]

                        mean_y = all_mean_stdev[k][1][0][index]
                        stdev_y = all_mean_stdev[k][1][1][index]

                        if str(stdev_x) == "Null":
                            temp_x[index] = temp_x[index]
                        elif float(stdev_x) == 0:
                            temp_x[index] = temp_x[index]
                        else:
                            temp_x[index] = (temp_x[index] - float(mean_x)) / float(stdev_x)

                        if str(stdev_y) == "Null":
                            temp_y[index] = temp_y[index]
                        elif float(stdev_y) == 0:
                            temp_y[index] = temp_y[index]
                        else:
                            temp_y[index] = (temp_y[index] - float(mean_y)) / float(stdev_y)

                    # build new array of normalized values
                    values = []
                    for index in range(len(temp_x)):
                        values.append(temp_x[index])
                        values.append(temp_y[index])
                        values.append(temp_c[index])

                    # copy the array of normalized values where it came from
                    data['people'][0][k] = values

                dictionary_file_path = data_dir_target / 'all_files_centralized.npy'
                last_folder = os.path.basename(os.path.normpath(dictionary_file_path.parent)) + "/" + str(
                    dictionary_file_path.name)


                print("Saving centralized results to %s " % last_folder)
                np.save(dictionary_file_path, all_files_dictionary)

                # ## Save our changes to JSON file
                jsonFile = open(data_dir_target / subdir / file, "w+")
                jsonFile.write(json.dumps(data))
                jsonFile.close()


if __name__ == '__main__':
    # origin json files directory
    if len(sys.argv) > 1:
        path_to_json_dir = sys.argv[1]
    else:
        print("Set json file directory")
        sys.exit()

    # target directory
    path_to_target_dir = ""
    if len(sys.argv) > 2:
        path_to_target_dir = sys.argv[2]
    try:
        norm = Normalize(path_to_json_dir, path_to_target_dir)
        start_time = time.time()
        norm.main()
        print("--- %.4s seconds ---" % (time.time() - start_time))
    except NameError:
        print("Set paths")
