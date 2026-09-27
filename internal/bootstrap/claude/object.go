package claude

import (
	"bytes"
	"encoding/json"
	"errors"
)

// object is a JSON object that keeps its key order, so a rewritten
// settings.json reads like the one jq left behind.
type object []member

type member struct {
	Key   string
	Value json.RawMessage
}

func parseObject(data []byte) (object, error) {
	dec := json.NewDecoder(bytes.NewReader(data))
	tok, err := dec.Token()
	if err != nil {
		return nil, err
	}
	if tok != json.Delim('{') {
		return nil, errors.New("want a JSON object")
	}
	obj := object{}
	for dec.More() {
		tok, err := dec.Token()
		if err != nil {
			return nil, err
		}
		var value json.RawMessage
		if err := dec.Decode(&value); err != nil {
			return nil, err
		}
		obj = append(obj, member{Key: tok.(string), Value: value})
	}
	if _, err := dec.Token(); err != nil {
		return nil, err
	}
	return obj, nil
}

func (o object) get(key string) (json.RawMessage, bool) {
	for _, m := range o {
		if m.Key == key {
			return m.Value, true
		}
	}
	return nil, false
}

// set replaces the value in place, or appends the key like jq does.
func (o *object) set(key string, value json.RawMessage) {
	for i := range *o {
		if (*o)[i].Key == key {
			(*o)[i].Value = value
			return
		}
	}
	*o = append(*o, member{Key: key, Value: value})
}

// marshal returns the object compacted.
func (o object) marshal() (json.RawMessage, error) {
	var b bytes.Buffer
	b.WriteByte('{')
	for i, m := range o {
		if i > 0 {
			b.WriteByte(',')
		}
		key, err := marshal(m.Key)
		if err != nil {
			return nil, err
		}
		b.Write(key)
		b.WriteByte(':')
		b.Write(m.Value)
	}
	b.WriteByte('}')
	var out bytes.Buffer
	if err := json.Compact(&out, b.Bytes()); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}

// marshal encodes without HTML escaping, as jq writes strings.
func marshal(v any) (json.RawMessage, error) {
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	return bytes.TrimSuffix(b.Bytes(), []byte("\n")), nil
}

func isNull(raw json.RawMessage) bool {
	return string(bytes.TrimSpace(raw)) == "null"
}
