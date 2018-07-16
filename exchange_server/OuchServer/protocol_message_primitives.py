import struct
import enum

class DuplicateFreeEnum(enum.Enum):
    # force unique values, as per docs:
    # https://docs.python.org/3/library/enum.html#duplicatefreeenum
    def __init__(self, *args, **kwargs):
        cls = self.__class__
        for element in cls:
            if element.value == self.value:
                raise ValueError(
                    'aliases not allowed in DuplicateFreeEnum: {} --> {}'
                    .format(element.name, self.name))

class ProtocolField(object):
    def __init__(self, type_spec, description):
        self._type_spec = type_spec
        self._description = description

    @property
    def type_spec(self):
        return self._type_spec

    @property
    def description(self):
        return self._description

    def __repr__(self):
        rep = ('ProtocolField({self._type_spec!r}, {self.description!r})'
                .format(self=self))
        return rep

    def __str__(self):
        return self._description

class ProtocolFieldEnum(ProtocolField, DuplicateFreeEnum):
    pass

class NamedFieldSequenceSerializerMeta(type):
    def __init__(cls, name, bases, namespace):
        cls._struct_formatter = struct.Struct(
            cls._wire_format +
            ''.join(cls._protocol_fields[field].type_spec
                    for field in cls.__slots__))
        super().__init__(name, bases, namespace)

    @property
    def size(cls):
        return cls._struct_formatter.size

class NamedFieldSequence(object, metaclass=NamedFieldSequenceSerializerMeta):
    _struct_formatter = None
    _protocol_fields = None
    _wire_format = '!'  # network byte order and no padding
    __slots__ = ()

    @classmethod
    def from_bytes(cls, source_bytes):
        return cls(*cls._struct_formatter.unpack(source_bytes))

    def to_bytes(self):
        return bytes(self)

    def __init__(self, *args, **kwargs):
        if args and kwargs:
            raise ValueError('NamedFieldSequence can only take one of positional or keyword arguments')
        elif len(args) == len(self.__slots__):
            for (slot, value) in zip(self.__slots__, args):
                setattr(self, slot, value)
        elif args:
            raise ValueError('%s has %d slots, got %d values'
                             % (self.__class__, len(self.__slots__), len(args)))

        else:  # kwargs
            for slot in self.__slots__:
                setattr(self, slot, kwargs.get(slot, None))

    def __bytes__(self):
        for slot in self.__slots__:
            assert getattr(self, slot) is not None, 'slot %s has value None' % (slot)
        return self._struct_formatter.pack(
            *(getattr(self, slot) for slot in self.__slots__))

    def __len__(self):
        return len(self.__slots__)
    def __iter__(self):
        yield from iter(self.__slots__)
    def iteritems(self):
        yield from ((s, getattr(self, s)) for s in self.__slots__)
    def __getitem__(self, key):
        if key in self.__slots__:
            return getattr(self, key)
        else:
            raise KeyError('key %s not found' % (key))
    def __setitem__(self, key, value):
        if key in self.__slots__:
            setattr(self, key, value)
        else:
            raise KeyError('key %s not found' % (key))
    def __delitem__(self, key):
        if key in self.__slots__:
            raise TypeError('%s has immutable keys' % (self.__class__.__name__))
        else:
            raise KeyError('key %s not found' % (key))

    def __contains__(self, key):
        return key in self.__slots__
    
    def __repr__(self):
        rep = ('NamedFieldSequence(' + ', '
                   .join('{key}={self[key]!r}' for key in self.__slots__) +
               ')')
        return rep

    def __str__(self):
        return ('[' + ', '
                .join(self[key] for key in self.__slots__) +
                ']')

class ProtocolMessage(object):
    _HeaderCls = None
    _PayloadBaseCls = None

    def __init__(self, message_type_spec, *args, **kwargs):
        self._message_type_spec = message_type_spec
        self.payload = message_type_spec.PayloadCls(*args, **kwargs)

    def to_bytes(self, header=False):
        return bytes(self) if header else bytes(self.payload)

    @classmethod
    def from_payload_bytes(cls, message_type_spec, payload_bytes):
        message = cls(message_type_spec)
        message.payload = message_type_spec.PayloadCls.from_bytes(payload_bytes)
        return message
    @classmethod
    def get_header_class(cls):
        return cls._HeaderCls
    @classmethod
    def get_payload_base_class(cls):
        return cls._PayloadBaseCls

    @property
    def header(self):
        return self._message_type_spec.header
    @property
    def message_type(self):
        return self._message_type_spec

    def __bytes__(self):
        return bytes(self._message_type_spec.header) + bytes(self.payload)

    def __len__(self):
        return len(self.payload)
    def __iter__(self):
        yield from iter(self.payload)
    def iteritems(self):
        yield from self.payload.iteritems()
    def __getitem__(self, key):
        return self.payload[key]
    def __setitem__(self, key, value):
        self.payload[key] = value
    def __delitem__(self, key):
        del self.payload[key]
    def __contains__(self, key):
        return key in self.payload
    
    def __repr__(self):
        payload_rep = repr(self.payload)
        payload_rep = payload_rep.partition('(')[-1]
        payload_rep = payload_rep.rpartition(')')[0]
        rep = ('ProtocolMessage({message_type_spec}, {payload_rep})'
               .format(type(self._message_type_spec), payload_rep))
        return rep

    def __str__(self):
        return '{self.header!s}: {self.payload!s}'.format(self=self)

class MessageTypeSpec(object):
    _MessageCls = None

    def __init__(self, header_field_values, payload_fields, name=None):
        if name is None:
            name = self.name
        cls = self.__class__
        HeaderCls = cls._MessageCls.get_header_class()
        PayloadBaseCls = cls._MessageCls.get_payload_base_class()
        self._header = HeaderCls(**header_field_values)
        self._PayloadCls = type(
            name, (PayloadBaseCls,),
            {'__slots__': payload_fields})

    def __call__(self, *args, **kwargs):
        return self._MessageCls(self, *args, **kwargs)

    def from_bytes(self, message_bytes, header=True):
        if header:
            header_len = self._MessageCls._HeaderCls.size
            header_bytes = message_bytes[:header_len]
            message_bytes = message_bytes[header_len:]
            if header_bytes != self.header_bytes:
                raise ValueError('header mismatch!')
        return self._MessageCls.from_payload_bytes(self, message_bytes)

    @classmethod
    def get_message_class(self):
        return self._MessageCls
    @property
    def header(self):
        return self._header
    @property
    def header_bytes(self):
        return bytes(self._header)
    @property
    def PayloadCls(self):
        return self._PayloadCls
    @property
    def header_size(self):
        return self._HeaderCls.get_header_class().size
    @property
    def payload_size(self):
        return self._PayloadCls.size
        
    def __repr__(self):
        header_spec = ('[' + ', '.join(repr(self._header[key])
                                       for key in self._header.__slots__) +
                       ']')
        payload_spec = '[' + ', '.join(self._PayloadCls.__slots__) + ']'
        rep = ('MessageTypeSpec({header_spec}, {payload_spec}, name={name!r})'
               .format(header_spec=header_spec, payload_spec=payload_spec,
                       payload_name=self._PayloadCls.__class__.__name__))
        return rep

    def __str__(self):
        return ('{self._header!s}: {field_names}'
                .format(self=self,
                        field_names=', '.join(self._PayloadCls.__slots__)))

def create_attr_lookup_mixin(cls_name, attr_name):
    lookup_table_name = '_{}_lookup_table'.format(attr_name)

    class LookupByAttrMixin(object):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            cls = self.__class__
            lookup_table = getattr(cls, lookup_table_name)
            attr_value = getattr(self, attr_name)
            if attr_value in lookup_table:
                raise ValueError('{}: attribute {} has duplicate value {}'
                                 .format(self.__class__.__name__, attr_name, attr_value))
            else:
                lookup_table[attr_value] = self

    def lookup(cls, attr_value):
        lookup_table = getattr(cls, lookup_table_name)
        return lookup_table[attr_value]

    return type(cls_name, (LookupByAttrMixin,),
               {('lookup_by_' + attr_name): classmethod(lookup),
                 lookup_table_name: dict()})