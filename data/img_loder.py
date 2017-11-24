import glob
import cv2
import numpy as np
import skvideo.io
import skvideo.datasets


def get_one_clip(lst, index, skip, length):
    return lst[index:index + length * skip:skip]


def get_clips(img_lst, skip, length):
    clips = [get_one_clip(img_lst, i, skip, length) for i in range(len(img_lst)) if
             len(get_one_clip(img_lst, i, skip, length)) == length]

    return clips


def get_pair(img_lst, pre, skip, length):
    A = get_clips(img_lst[:][:-pre], skip, length)
    B = get_clips(img_lst[pre:], skip, length)
    return A, B


read_ = lambda x: cv2.resize(cv2.imread(x)[:, int(1242 / 2 - 375 / 2):int(1242 / 2 + 375 / 2), ::-1], (256, 256))
read_gray =  lambda x: cv2.resize(cv2.imread(x.replace("_rgb","_depthgt") , 0)[:, int(1242 / 2 - 375 / 2):int(1242 / 2 + 375 / 2)], (256, 256))

def gen_np(c,in_chanel,out_chanel):
    #     print(c)
    img1 = [read_(i) for i in c[0]]
    img2 = [read_(i) for i in c[1]]
    if in_chanel == 4:
        depth1 = [read_gray(i).reshape(256,256,1) for i in c[0]]
        depth2 = [read_gray(i).reshape(256,256,1) for i in c[1]]
        img1 = [ np.concatenate([i,j],axis = -1 ) for i,j in zip(img1 ,depth1 )]
        img2 = [np.concatenate([i, j], axis = -1) for i, j in zip(img2, depth2)]

    v = np.asarray([img1, img2])
    v = np.transpose(v, (0, 4, 1, 2, 3))
    #     v.transpose(0,4,1,2,3)
    return v


def dump(img_lst, dirpath = 'data', start = 0, skip = 2, length = 7, pre = 2 ,in_chanel =3,out_chanel=3):
    a, b = get_pair(img_lst, pre, skip, length)
    task = [(i, j) for i, j in zip(a, b)]
    gen = (gen_np(j ,in_chanel,out_chanel) for j in task)
    return gen


def data_gen(data_path, opt):
    skip = opt.skip
    length = opt.depth
    pre = opt.depth
    in_chanel = opt.input_nc
    out_chanel = opt.output_nc
    start = 0
    img_lst = glob.glob(data_path + "**.png")
    img_lst.sort()
    # print(img_lst)
    gen = dump(img_lst, 'video/{}{}'.format(*data_path.split('/')[-3:-1]), start, skip, length, pre ,in_chanel,out_chanel)
    return data_path, gen


#########################
# Video Data Generation
#########################


def gen_frame(i, frames_lst, length, overlap):
    A = np.asarray(frames_lst[i:i + length])
    B = np.asarray(frames_lst[i + length - overlap:i + length * 2 - overlap])
    v = np.asarray([A, B])
    v = np.transpose(v, (0, 4, 1, 2, 3))
    return v


def video_data_gen(vid_path, opt):
    skip = opt.skip
    length = opt.depth
    overlap = opt.overlap
    #if not os.path.exists(out_path):
        #os.mkdir(out_path)

    #vid_name = os.path.basename(vid_path).split('.')[0]
    videogen = skvideo.io.vreader(vid_path)

    frames_lst = [cv2.resize(frame[:, 40:280, :], (256, 256))
                  for i, frame in enumerate(videogen) if i % skip == 0]

    n = int(len(frames_lst) / (length * 2))

    gen = (gen_frame(i, frames_lst=frames_lst, length=length, overlap=overlap) for i in range(n))

    return vid_path, gen