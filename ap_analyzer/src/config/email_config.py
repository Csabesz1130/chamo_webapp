"""
E-mail szolgáltatás konfigurációs beállításai.
"""
import os
from typing import Optional
from pydantic import BaseModel, EmailStr, validator

class EmailConfig(BaseModel):
    """E-mail konfigurációs osztály."""
    
    # Általános beállítások
    provider: str = "smtp"  # "smtp", "ses", vagy "postmark"
    from_email: EmailStr
    reply_to_email: Optional[EmailStr] = None
    
    # AWS SES beállítások
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Postmark beállítások
    postmark_token: Optional[str] = None
    
    # SMTP beállítások
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_use_tls: bool = True
    
    # Digest beállítások
    digest_subject_template: str = "Heti tudományos cikkek ajánlója - {date}"
    max_articles_per_digest: int = 5
    
    @validator('provider')
    def validate_provider(cls, v):
        """Ellenőrzi a provider értékét."""
        if v not in ['smtp', 'ses', 'postmark']:
            raise ValueError('Az e-mail provider csak "smtp", "ses", vagy "postmark" lehet')
        return v
    
    @validator('aws_region', 'aws_access_key_id', 'aws_secret_access_key')
    def validate_aws_config(cls, v, values, field):
        """Ellenőrzi az AWS beállításokat."""
        if values.get('provider') == 'ses' and not v:
            raise ValueError(f'Az {field.name} kötelező SES használata esetén')
        return v
    
    @validator('postmark_token')
    def validate_postmark_config(cls, v, values):
        """Ellenőrzi a Postmark beállításokat."""
        if values.get('provider') == 'postmark' and not v:
            raise ValueError('A postmark_token kötelező Postmark használata esetén')
        return v
    
    @validator('smtp_host', 'smtp_port')
    def validate_smtp_config(cls, v, values, field):
        """Ellenőrzi az SMTP beállításokat."""
        if values.get('provider') == 'smtp' and not v:
            raise ValueError(f'Az {field.name} kötelező SMTP használata esetén')
        return v
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """
        Létrehoz egy konfigurációt a környezeti változókból.
        
        Returns:
            EmailConfig: A konfigurációs objektum
        """
        config_dict = {
            'provider': os.getenv('EMAIL_PROVIDER', 'smtp'),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@example.com'),
            'reply_to_email': os.getenv('REPLY_TO_EMAIL'),
            
            # AWS SES
            'aws_region': os.getenv('AWS_REGION'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            
            # Postmark
            'postmark_token': os.getenv('POSTMARK_TOKEN'),
            
            # SMTP
            'smtp_host': os.getenv('SMTP_HOST'),
            'smtp_port': int(os.getenv('SMTP_PORT', 0)) if os.getenv('SMTP_PORT') else None,
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_pass': os.getenv('SMTP_PASS'),
            'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            
            # Digest
            'digest_subject_template': os.getenv(
                'DIGEST_SUBJECT_TEMPLATE',
                'Heti tudományos cikkek ajánlója - {date}'
            ),
            'max_articles_per_digest': int(os.getenv('MAX_ARTICLES_PER_DIGEST', '5'))
        }
        
        return cls(**config_dict) 