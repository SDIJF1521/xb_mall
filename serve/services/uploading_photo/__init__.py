import imghdr
from ..user_info import UserInfo

class UploadingPhoto:
    def __init__(self,file_content:bytes):
        self.file_content = file_content

    async def uploading(self,token:str):
        '''
        token:str
        '''
        token_select = UserInfo(token)
        token = await token_select.token_analysis()
        print(imghdr.what(None,h=self.file_content))
        if imghdr.what(None,h=self.file_content) is not None:
            if token['current']:
                with open(f'./img/{token["user"]}.jpg','wb') as f:
                    f.write(self.file_content)
                return {'query':'UPDATE personal_details SET HeadPortrait = %s WHERE user = %s;','params':(f'./img/{token["user"]}.jpg',token["user"]),'current':True}
            else:
                return {'mag':'上传失败无法找到改用户','current':True}
        else:
            return {'mag':'上传的文件不是图片,非法数据','current':False}