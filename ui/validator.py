

class Validator:
    @staticmethod
    def validate_is_numeric(new_text: str) -> bool:
        """
        Validates that the text is composed of only digits.
        Allows an empty field.
        """
        if new_text == "":
            return True
        return new_text.isdigit()
    
    @staticmethod
    def validate_numeric_range(min_val: str, max_val: str, new_text: str) -> bool:
        """
        Validates that the text is an integer within a specified range.
        Allows an empty field.
        """
        if new_text == "":
            return True
        
        try:
            value = int(new_text)
            # Only check min_val if it's a valid number string
            if min_val is not None and min_val.strip() != "" and value < int(min_val):
                return False
            # Only check max_val if it's a valid number string
            if max_val is not None and max_val.strip() != "" and value > int(max_val):
                return False
            return True
        except ValueError:
            return False


    @staticmethod
    def validate_string_length(max_len:str, string:str)->bool:
        """returns True if the string length is less than the max allowed.
        
        """
        return len(string) <= int(max_len)
