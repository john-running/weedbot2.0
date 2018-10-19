# weedbot2.0

This repository contains files required to make weedbot find weeds and share results.

drive_and_classify.py contains code to tell weedbot to drive along a prescribed path, capture images of
whatever it is driving over at .5 second intervals, classify those images and storing them in a SQLlite database GS.db. 

Main.py runs a local Flask-based Webserver on Weedbot so that the results can be viewed in a web browser.

Classification is accomplished using Tensorflow on a pre-trained model called mobilenet that was further trained with photos taken by weedbot.  The current retrained model is in tf_files/retrained_graph.pb.  The code was adapted from https://github.com/EN10/TensorFlowForPoets

