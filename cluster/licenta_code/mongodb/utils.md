To insert new field in documents:

```
db.scrapped_test_unique.updateMany(
    {},
    {
        $set :{
            "link" : ''
        }
    }
)
```
