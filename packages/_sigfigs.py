from types import ModuleType
import decimal


class Sigfigs(ModuleType):
    _small_e_threshold = -4
    _large_e_threshold = 4
    def __call__(self, n, places):
        if hasattr(n, "magnitude") :
            return sigfigs(n.magnitude, places)
        neg, digits, decimal_place = decimal.Decimal(n).as_tuple()
        decimal_place += len(digits)
        digits = list(digits)
        if places<len(digits) and digits[places]>=5:
            digits[places-1] +=1
        digits = digits[:places]
        method = self._regular_notation
        if len(digits)<places:
            digits.extend([0]*(places-len(digits)))
            
        if decimal_place<=0:
            #we have 0.something, no ambiquity but will still use e notation if too many leading 0s
            if decimal_place<self._small_e_threshold:
                method = self._e_notation
        elif decimal_place<len(digits):
            #the decimal is within the digits, no ambiquity
            pass
        elif decimal_place==len(digits):
            #we have precision to the units place, use regular but add a trailing . if the last digit is 0
            if digits[-1]==0:
                #use trailing decimal to indicate that the trailing 0s are significant
                return self._regular_notation(neg, digits, decimal_place)+"."
            
        #have extra zeros after decimal,
        #use standard notation as long as we don't have too many trailing zeros
        # and that the last digit isn't 0 otherwise it'd be ambiguous.
        elif (decimal_place-len(digits) > self._large_e_threshold
              or digits[-1]==0):
            method = self._e_notation
        return method(neg, digits, decimal_place)
    
    @classmethod
    def _e_notation(cls,neg, digits,d_place):
        sgn = "-" if neg else ""
        exp = d_place-1
        num = cls._regular_notation(neg, digits, 1)
        return "{}{}e{}".format(sgn, num, exp)
    @staticmethod
    def _regular_notation(neg, digits, d_place):
        sgn = "-" if neg else ""
        num = "".join(map(str,digits))
        if d_place<=0:
            num = "0."+"0"*-d_place + num
        elif d_place<len(digits):
            num = num[:d_place]+"."+num[d_place:]
        else:
            num+= "0"*(d_place-len(digits))
        return sgn+num
        
    

sigfigs = Sigfigs("sigfigs")
        
