"""Map the already configured personal mailbox to original skill env names."""
import json, os, sys
from pathlib import Path

def main():
    cfg=json.loads(Path('/run/secrets/services.json').read_text(encoding='utf-8-sig'))
    mail=cfg.get('mail',{})
    values=dict(IMAP_HOST=mail.get('imap_host'),IMAP_PORT=mail.get('imap_port'),
        IMAP_USER=mail.get('address'),IMAP_PASS=mail.get('authorization_code'),IMAP_TLS='true',
        SMTP_HOST=mail.get('smtp_host'),SMTP_PORT=mail.get('smtp_port'),
        SMTP_USER=mail.get('address'),SMTP_PASS=mail.get('authorization_code'),SMTP_SECURE='true')
    for k,v in values.items():
        if v is not None:os.environ[k]=str(v)
    os.environ['NODE_PATH']='/usr/local/lib/node_modules'
    os.execv(sys.executable,[sys.executable]+sys.argv[1:])

if __name__=='__main__':main()
