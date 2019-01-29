from __future__ import print_function, absolute_import
from reid.bottom_up import *
from reid import datasets
from reid import models
import numpy as np
import argparse
import os, sys, time
from reid.utils.logging import Logger
import os.path as osp
from torch.backends import cudnn

def main(args):
    cudnn.benchmark = True
    cudnn.enabled = True
    
    save_path = args.logs_dir
    sys.stdout = Logger(osp.join(args.logs_dir, 'log'+ str(args.merge_percent)+ time.strftime(".%m_%d_%H:%M:%S") + '.txt'))

    # get all unlabeled data for training
    dataset_all = datasets.create(args.dataset, osp.join(args.data_dir, args.dataset))
    new_train_data = change_to_unlabel(dataset_all)

    label = []
    for idx, data in enumerate(new_train_data):
        data[3] = idx # data[3] is the label of the data array
        label.append(data[3])  # index

    new_train_data = new_train_data
    num_train_ids = len(np.unique(np.array(label)))
    nums_to_merge = int(num_train_ids * args.merge_percent)

    BuMain = Bottom_up(model_name=args.arch, batch_size=args.batch_size, 
            num_classes=num_train_ids,
            dataset=dataset_all,
            u_data=new_train_data, save_path=args.logs_dir, max_frames=args.max_frames,
            embeding_fea_size=args.fea)


    initial_steps = 20
    later_steps = 2 


    total_step = int(1/args.merge_percent)
    for step in range(total_step):
        print('step: ',step)

        BuMain.train(new_train_data, step, loss=args.loss) 

        BuMain.evaluate(dataset_all.query, dataset_all.gallery)

        if step < total_step - 1:
            # get new train data for the next iteration
            print('----------------------------------------bottom-up clustering------------------------------------------------')
            label, new_train_data = BuMain.get_new_train_data(label, nums_to_merge, size_penalty=args.size_penalty)
            print('\n\n')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Exploit the Unknown Gradually')
    parser.add_argument('-d', '--dataset', type=str, default='mars',
                        choices=datasets.names())
    parser.add_argument('-b', '--batch-size', type=int, default=16)  
    parser.add_argument('-f', '--fea', type=int, default=2048)
    parser.add_argument('-a', '--arch', type=str, default='avg_pool',choices=models.names())
    working_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument('--data_dir', type=str, metavar='PATH',
                        default=os.path.join(working_dir,'data'))
    parser.add_argument('--logs_dir', type=str, metavar='PATH',
                        default=os.path.join(working_dir,'logs'))
    parser.add_argument('--max_frames', type=int, default=900)
    parser.add_argument('--loss', type=str, default='ExLoss')
    parser.add_argument('-m', '--momentum', type=float, default=0.5)
    parser.add_argument('-e1', '--epochs1', type=int, default=20)
    parser.add_argument('-e2', '--epochs2', type=int, default=2)
    parser.add_argument('-s', '--step_size', type=int, default=55)
    parser.add_argument('--size_penalty',type=float, default=0.005)
    parser.add_argument('-mp', '--merge_percent',type=float, default=0.05)
    main(parser.parse_args())

