"""
邮箱工具
    - send_email: 发送邮件
"""

import aiosmtplib
import mimetypes
from pathlib import Path
from typing import Optional, List
from email.message import EmailMessage
from email.utils import make_msgid
from utils.logger_manager import LoggerManager
from configs.general_config import FilePath

logger = LoggerManager.get_logger(__name__)


class EmailTools:
    def __init__(self,
    smtp_server:str,
    smtp_port:int,
    username:str,
    password:str,
    domain:str,):
        """
        初始化邮箱工具
        Args:
            smtp_server:  SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 用户名
            password: 密码
            domain: 域名
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.domain = domain
        self.root_path = FilePath.ROOT_PATH

    async def send_email(
        self,
        to_addrs: list[str],
        subject: str,
        content: str,
        message_id: Optional(str) = None,
        attachments: Optional[List[str]] = None,
    ):
        """
        发送邮件
        Args:
            to_addrs: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            message_id: 消息ID
        Returns:
            dict: 发送结果
        """
        addrs_err = self._validte_to_addrs(to_addrs)
        if not addrs_err["status"]:
            return {"status": False, "message": addrs_err.get("message")}
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = ",".join(to_addrs)
        msg['Message-ID'] = make_msgid(idstring=message_id, domain=self.domain)
        msg.set_content(content)

        if attachments and isinstance(attachments, list):
            attachment_err = self._add_attachments(msg, attachments)
            if not attachment_err["status"]:
                return {"status": False, "message": attachment_err.get("message")}

        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True,
            ) as server:
                try:
                    await server.send_message(
                        msg,
                        sender=self.username,
                        recipients=to_addrs,
                        mail_options=["RET=HDRS"],
                        rcpt_options=["NOTIFY=FAILURE,DELAY"],
                    )

                except aiosmtplib.SMTPResponseException:
                    await server.send_message(
                        msg,
                        sender=self.username,
                        recipients=to_addrs,
                    )
            return {"status": True, "message_id": msg['Message-ID']}
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return {"status": False, "message": str(e)}

    def _validte_to_addrs(self, to_addrs: list[str]):
        """
        验证收件人地址
        Args:
            to_addrs: 收件人列表
        Returns:
            list[str]: 验证后的收件人列表
        """
        if not to_addrs:
            return {"status": False, "message": "收件人地址不能为空"}
        for addr in to_addrs:
            if not isinstance(addr, str) or not addr.strip():
                return {"status": False, "message": f"无效收件人: {addr!r}"}
            if "@" not in addr or "." not in addr:
                return {"status": False, "message": f"无效收件人: {addr}"}

        return {"status": True, "message": "收件人地址验证成功"}

    def _add_attachments(
            self,
            msg: EmailMessage,
            attachments: list[str],):
        """
        添加附件
        Args:
            msg: 邮件消息
            attachments: 附件列表
        """
        for path in attachments:
            p = Path(self.root_path, path)
            if not p.is_file():
                return {"status": False, "message": f"文件不存在: {path}"}
            data = p.read_bytes()
            ctype, _ = mimetypes.guess_type(p.name)
            if ctype is None:
                maintype, subtype = "application", "octet-stream"
            else:
                maintype, subtype = ctype.split("/", 1)
            msg.add_attachment(data, maintype=maintype,
                               subtype=subtype, filename=p.name)
        return {"status": True, "message": "附件添加成功"}
