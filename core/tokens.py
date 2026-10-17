from django.contrib.auth.tokens import PasswordResetTokenGenerator


class VerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "stackquay.email-verification"

    def _make_hash_value(self, user, timestamp):
        return (
            super()._make_hash_value(user, timestamp)
            + str(user.is_active)
            + str(user.email_verified)
        )


verification_tokens = VerificationTokenGenerator()
