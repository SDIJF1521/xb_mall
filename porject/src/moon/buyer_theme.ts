export default class BuyerTheme{
    //切换主题
    toggleTheme(isDark:boolean){
        if(isDark){
            document.documentElement.classList.add('dark')
        }else{
            document.documentElement.classList.remove('dark')
        }
    }
}