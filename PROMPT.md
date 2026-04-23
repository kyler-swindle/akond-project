## zero-shot
```
def zero_shot_prompt(chunk: str) -> str:
    return f"""
        Extract Key Data Elements (KDEs) and their requirements.

        Return ONLY valid YAML.

        Format:
        element1:
        name: <KDE name>
        requirements:
            - <requirement>

        Rules:
        - No markdown
        - Do NOT use ```yaml
        - No empty requirements
        - No explanations

        TEXT:
        {chunk}
    """
```

## few-shot
```
def one_shot_prompt(chunk: str) -> str:
    return f"""
        Extract Key Data Elements (KDEs) and their requirements.

        Return ONLY valid YAML.

        Format:
        element1:
        name: <KDE name>
        requirements:
            - <requirement>

        Example:

        Input:
        The system must authenticate users using MFA and log all access attempts.

        Output:
        element1:
        name: Authentication
        requirements:
            - Must support multi-factor authentication
            - Must log all access attempts

        Rules:
        - No markdown
        - Do NOT use ```yaml
        - No empty requirements
        - No explanations

        TEXT:
        {chunk}
    """
```

## chain-of-thought
def cot_prompt(chunk: str) -> str:
    return f"""
        Extract Key Data Elements (KDEs) and their requirements.

        Follow this process internally:
        1. Identify all key data elements in the text
        2. Extract requirements associated with each element
        3. Normalize and remove duplicates
        4. Ensure each requirement is actionable and explicit

        IMPORTANT:
        - Do NOT output reasoning
        - Do NOT explain steps
        - Output ONLY valid YAML

        Format:
        element1:
        name: <KDE name>
        requirements:
            - <requirement>

        Rules:
        - No markdown
        - Do NOT use ```yaml
        - No empty requirements
        - No explanations

        TEXT:
        {chunk}
    """