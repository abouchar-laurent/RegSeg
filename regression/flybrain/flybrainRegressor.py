import os
import numpy as np
from tifffile import imread

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.externals import joblib
import pylab as pl
import sys

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(ROOT_PATH,'src','python'))
import surface_reconstruction as sr

max_dist = 15
max_training_size = 10000000  # Upper bound on the number of samples used for training.


ROOT_DATA = '/Users/abouchar/ownCloud/ProjectRegSeg/data/' # Set to your local path

training_set = range(1,9)  # Indices of images to use for training.

learner = GradientBoostingRegressor
learner_params = {'n_estimators':100}

n_features = 61

TEST_REGRESSOR = True







### 0. Set up a few variables

first_nb = "%03d" % training_set[0]
last_nb = "%03d" % training_set[-1]
saved_regressor_name = 'regressorOn'+first_nb+'to'+last_nb
regressor_path = os.path.join(ROOT_DATA,'Flybrain',saved_regressor_name)


ROOT = os.path.join(ROOT_DATA,'Flybrain','GroundTruthCenterlines')
ROOT_FTR = os.path.join(ROOT_DATA,'Flybrain','Features')
ROOT_IMG = os.path.join(ROOT_DATA,'Flybrain','RawData')
ROOT_DST = os.path.join(ROOT_DATA,'Flybrain','GroundTruth')
files = [f for f in os.listdir(ROOT) if f.endswith('tif')]


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

prog = os.path.join(ROOT_PATH,'..','src','cpp','graph_cut')

# list of files
files_ftr = [f for f in os.listdir(ROOT_FTR) if f.endswith('tif')]
files_dst = [f for f in os.listdir(ROOT_DST) if f.endswith('tif')]
files_img = [f for f in os.listdir(ROOT_IMG) if f.endswith('tif')]









### 1. If regressor is saved, load it, otherwise train a new one.

indices = ["%03d" % i for i in training_set]
training_feat = [f for f in files_ftr if f[:3] in indices]
training_dist = [f for f in files_dst if f[:3] in indices]

if os.path.exists(regressor_path) and False:
    
    clf = joblib.load(regressor_path)
    
else:
    
    features = np.empty((0,n_features))
    ground_truth = np.empty((0))
    count = 0
    
    for features_img, dist_img in zip(training_feat, training_dist):
        count += 1
        features = np.concatenate((features, imread(os.path.join(ROOT_FTR, features_img))),axis=0)
        ground_truth = np.concatenate((ground_truth,np.minimum(imread(os.path.join(ROOT_DST, dist_img)),max_dist).flatten()))
        
        if np.size(ground_truth) > max_training_size:
            
            features = features[:max_training_size,:]
            ground_truth = ground_truth[:max_training_size]
            print "Used " + str(count) + " images for training before reaching max samples."
            break
            
    
    clf = learner(**learner_params)
    
    clf.fit(features,ground_truth)
    
    joblib.dump(clf, regressor_path) 
    



### 2. Optionally, test trained regressor and plot results:
if TEST_REGRESSOR:
    
    trained_data = np.random.choice(training_feat)
    trained_img = trained_data[:-13] + '.tif'
    trained_truth = trained_data[:-13] + '_dst.tif'

    features = imread(os.path.join(ROOT_FTR, trained_data))
    img_shape = imread(os.path.join(ROOT_IMG, trained_img)).shape
    true_dist = np.minimum(imread(os.path.join(ROOT_DST, trained_truth)),max_dist)
    
    prediction = clf.predict(features).reshape(img_shape)
    
    print "Regressor on one of the training images:\n\tL1: %.5f\n\tL2: %.5f" % (sr.score(prediction,true_dist,score='L1'), sr.score(prediction,true_dist,score='L2'))


    if len(training_feat) < len(files_ftr): # Test set is not empty.
        
        test_data = np.random.choice([f for f in files_ftr if f not in training_feat])
        test_img = test_data[:-13] + '.tif'
        test_truth = test_data[:-13] + '_dst.tif'

        features = imread(os.path.join(ROOT_FTR, test_data))
        img_shape = imread(os.path.join(ROOT_IMG, test_img)).shape
        true_dist = np.minimum(imread(os.path.join(ROOT_DST, test_truth)),max_dist)
        
        prediction = clf.predict(features).reshape(img_shape)
        
        print "Regressor on a test images:\n\tL1: %.5f\n\tL2: %.5f" % (sr.score(prediction,true_dist,score='L1'), sr.score(prediction,true_dist,score='L2'))

        import pylab
        pl.figure()
        pl.subplot(1,3,1)
        pl.imshow(true_dist[:,:,int(img_shape[-1]*0.5)],vmin=0,vmax=max_dist)
        pl.xticks([])
        pl.yticks([])
        pl.title('Ground Truth')
        pl.subplot(1,3,2)
        pl.imshow(prediction[:,:,int(img_shape[-1]*0.5)],vmin=0,vmax=max_dist)
        pl.xticks([])
        pl.yticks([])
        pl.title('Prediction')
        pl.subplot(1,3,3)
        pl.imshow(prediction[:,:,int(img_shape[-1]*0.5)])
        pl.xticks([])
        pl.yticks([])
        pl.title('Prediction Scaled')
        pl.show()