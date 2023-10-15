import cv2


FOURCC_MP4 = *'mp4v',
FOURCC_MOV = *'mp4v',
FOURCC_XVID = *'XVID',


def crop_video(src_path: str, dst_path: str, fourcc: list[str], start_frame: int, end_frame: int) -> None:
	video = cv2.VideoCapture(src_path)

	fps = video.get(cv2.CAP_PROP_FPS)
	width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

	fourcc = cv2.VideoWriter_fourcc(fourcc)
	out = cv2.VideoWriter(dst_path, fourcc, fps, (width, height))

	for i in range(end_frame + 1):
		ret, frame = video.read()
		if i < start_frame:
			continue
		if not ret:
			break

		out.write(frame)

	video.release()
	out.release()
