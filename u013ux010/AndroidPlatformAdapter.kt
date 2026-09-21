package nexus.android.c002

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.net.Uri
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

class AndroidPlatformAdapter(
    private val activity: Activity,
    private val navigate: (String) -> Unit
) {
    private var drawer: View? = null
    private var backdrop: View? = null
    private var contextPanel: View? = null
    private var settingsPanel: View? = null

    fun install() {
        val root = activity.findViewById<ViewGroup>(android.R.id.content)
        val d = activity.resources.displayMetrics.density

        val shade = View(activity).apply {
            setBackgroundColor(Color.argb(80,0,0,0))
            visibility = View.GONE
            setOnClickListener { closeMenu() }
        }
        root.addView(shade, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        backdrop = shade

        val menu = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding((12*d).toInt(), (12*d).toInt(), (12*d).toInt(), (12*d).toInt())
            background = ColorDrawable(Color.WHITE)
            visibility = View.GONE
            elevation = 16*d
        }
        root.addView(menu, FrameLayout.LayoutParams((260*d).toInt(), ViewGroup.LayoutParams.MATCH_PARENT, Gravity.START))
        drawer = menu

        menu.addView(label("NEXUS",18f))
        addNav(menu,"＋ Nouveau","home")
        addNav(menu,"Mes travaux","works")
        addNav(menu,"Fact Check","fact")
        addNav(menu,"Cartes","maps")
        menu.addView(label("TRAVAIL LOCAL",10f))
        addNav(menu,"Sujets persistants","subjects")
        addNav(menu,"Analyses locales","analyses")
        addNav(menu,"Archives","archives")
        addNav(menu,"NEXUS Context","context")
        addNav(menu,"Paramètres","settings")

        val trigger = Button(activity).apply {
            text = "☰"
            textSize = 18f
            contentDescription = "Ouvrir le menu NEXUS"
            setOnClickListener { toggleMenu() }
            elevation = 20*d
        }
        root.addView(trigger, FrameLayout.LayoutParams((52*d).toInt(),(52*d).toInt(),Gravity.START or Gravity.TOP).apply {
            leftMargin=(6*d).toInt(); topMargin=(6*d).toInt()
        })

        contextPanel = panel(root,"NEXUS Context","Contexte courant NEXUS. Les capacités restent celles du runtime validé.")
        settingsPanel = panel(root,"Paramètres","Options de présentation plateforme. Aucun réglage ne modifie le moteur NEXUS.")
    }

    private fun label(value:String,size:Float)=TextView(activity).apply {
        text=value; textSize=size; setTextColor(Color.rgb(32,33,35)); setPadding(12,14,12,14)
    }

    private fun addNav(parent:LinearLayout,title:String,destination:String) {
        parent.addView(Button(activity).apply {
            text=title; isAllCaps=false; gravity=Gravity.START or Gravity.CENTER_VERTICAL
            setOnClickListener {
                when(destination) {
                    "context" -> showPanel(contextPanel)
                    "settings" -> showPanel(settingsPanel)
                    else -> navigate(destination)
                }
                closeMenu()
            }
        })
    }

    private fun panel(root:ViewGroup,title:String,body:String):View {
        lateinit var box: LinearLayout
        box = LinearLayout(activity).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(20,20,20,20)
            background=ColorDrawable(Color.WHITE)
            elevation=18f
            visibility=View.GONE
            addView(label(title,18f))
            addView(label(body,14f))
            addView(Button(activity).apply {
                text="Fermer"; isAllCaps=false
                setOnClickListener { box.visibility=View.GONE }
            })
        }
        root.addView(box,FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT,Gravity.TOP).apply {
            leftMargin=24; rightMargin=24; topMargin=72
        })
        return box
    }

    private fun showPanel(panel:View?) {
        contextPanel?.visibility=View.GONE
        settingsPanel?.visibility=View.GONE
        panel?.visibility=View.VISIBLE
    }

    fun toggleMenu() {
        val open=drawer?.visibility!=View.VISIBLE
        drawer?.visibility=if(open) View.VISIBLE else View.GONE
        backdrop?.visibility=if(open) View.VISIBLE else View.GONE
    }
    fun closeMenu(){ drawer?.visibility=View.GONE; backdrop?.visibility=View.GONE }

    fun handleSystemBack():Boolean {
        if(drawer?.visibility==View.VISIBLE){closeMenu();return true}
        if(contextPanel?.visibility==View.VISIBLE){contextPanel?.visibility=View.GONE;return true}
        if(settingsPanel?.visibility==View.VISIBLE){settingsPanel?.visibility=View.GONE;return true}
        return false
    }

    fun openExternalUrl(url:String){ activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }
    fun viewportInfo():Map<String,Int> {
        val dm=activity.resources.displayMetrics
        return mapOf("widthPx" to dm.widthPixels,"heightPx" to dm.heightPixels,"densityDpi" to dm.densityDpi)
    }
    fun capabilities():Map<String,Boolean> = mapOf(
        "externalUrl" to true,"platformStorage" to true,"systemBack" to true,"safeAreaAware" to true
    )
    fun readPlatformStorage(key:String):String? =
        activity.getSharedPreferences("nexus_u013_platform",Context.MODE_PRIVATE).getString(key,null)
    fun writePlatformStorage(key:String,value:String) {
        activity.getSharedPreferences("nexus_u013_platform",Context.MODE_PRIVATE).edit().putString(key,value).apply()
    }
}
